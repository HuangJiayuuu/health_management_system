from app import app, db
from flask import jsonify,render_template, flash, redirect, url_for, request, abort
from app.forms import (LoginForm, RegistrationForm, EditProfileForm, GoalForm, 
                       AddExerciseGoalForm, SleepForm, ExerciseForm, DietForm)
from flask_login import current_user, login_user, logout_user, login_required
from app.models import User, SleepRecord, ExerciseRecord, DietRecord, Goal, ExerciseGoal
from datetime import datetime, timedelta
from urllib.parse import urlsplit
import matplotlib.pyplot as plt
import io
import base64
from collections import defaultdict
import os
import requests
from flask import session

@app.route('/')
@app.route('/index')
@login_required
def index():
    user_goal = current_user.goal
    exercise_goals = current_user.exercise_goals.all()
    progress_data = {}
    alert_messages = []  # 新增：用于存放预警信息

    today = datetime.utcnow().date()
    monday = today - timedelta(days=today.weekday())
    next_monday = monday + timedelta(days=7)
    last_7_days = [monday + timedelta(days=i) for i in range(0, 7)]
    days_so_far = (today - monday).days + 1  # 本周已过去天数（含今天）

    # --- Process General Goals ---
    if user_goal:
        # Sleep progress
        if user_goal.target_sleep_hours:
            sleep_records = current_user.sleep_records.filter(
                SleepRecord.sleep_time >= datetime.combine(monday, datetime.min.time()),
                SleepRecord.sleep_time < datetime.combine(today + timedelta(days=1), datetime.min.time())
            ).all()
            total_sleep = sum(r.duration for r in sleep_records)
            avg_sleep = total_sleep / days_so_far if days_so_far > 0 else 0
            progress_data['sleep'] = {
                'current': avg_sleep,
                'target': user_goal.target_sleep_hours,
                'progress': (avg_sleep / user_goal.target_sleep_hours) * 100 if user_goal.target_sleep_hours > 0 else 0
            }
        
        # Calorie progress (lower is better)
        if user_goal.target_calorie_intake:
            diet_records = current_user.diet_records.filter(
                DietRecord.timestamp >= datetime.combine(monday, datetime.min.time()),
                DietRecord.timestamp < datetime.combine(today + timedelta(days=1), datetime.min.time())
            ).all()
            total_calories = sum(r.calories for r in diet_records)
            avg_calories = total_calories / days_so_far if days_so_far > 0 else 0
            progress_data['calories'] = {
                'current': avg_calories,
                'target': user_goal.target_calorie_intake,
                'progress': (user_goal.target_calorie_intake / avg_calories) * 100 if avg_calories > 0 else 100
            }

    # --- Process Exercise Goals ---
    exercise_progress_list = []
    if exercise_goals:
        exercise_records_this_week = current_user.exercise_records.filter(
            ExerciseRecord.timestamp >= datetime.combine(monday, datetime.min.time()),
            ExerciseRecord.timestamp < datetime.combine(next_monday, datetime.min.time())
        ).all()
        for goal in exercise_goals:
            current_value = 0
            
            # Filter records relevant to the specific goal if an exercise_type is specified
            relevant_records = exercise_records_this_week
            if goal.exercise_type:
                relevant_records = [r for r in exercise_records_this_week if r.exercise_type == goal.exercise_type]

            # Calculate progress based on goal type
            if goal.goal_type == 'duration':
                current_value = sum(r.duration for r in relevant_records)
            elif goal.goal_type == 'frequency':
                current_value = len(relevant_records)
            elif goal.goal_type == 'calories':
                current_value = sum(r.calories_burned for r in relevant_records)

            exercise_progress_list.append({
                'goal': goal,
                'current': current_value,
                'target': goal.target_value,
                'progress': (current_value / goal.target_value) * 100 if goal.target_value > 0 else 0
            })
    
    # ========== 异常预警功能修正（连续三天不达标才警告） ==========
    # 1. 睡眠预警：最近三天连续都睡眠不足才警告
    if user_goal and user_goal.target_sleep_hours:
        min_sleep = user_goal.target_sleep_hours
        past_3_days = [(today - timedelta(days=i)) for i in range(3)]
        records = current_user.sleep_records.filter(
            SleepRecord.wakeup_time >= datetime.combine(today - timedelta(days=2), datetime.min.time()),
            SleepRecord.wakeup_time <= datetime.combine(today, datetime.max.time())
        ).all()
        daily_sleep = {d: 0 for d in past_3_days}
        for r in records:
            d = r.wakeup_time.date()
            if d in daily_sleep:
                daily_sleep[d] += r.duration
        # 检查三天是否连续都不达标
        all_days_insufficient = True
        for d in past_3_days:
            if daily_sleep[d] >= min_sleep:
                all_days_insufficient = False
                break
        if all_days_insufficient:
            alert_messages.append(f"警告：你最近三天连续睡眠不足（低于设定目标{min_sleep}小时），请注意休息！")

    # 2. 运动预警：最近三天连续都未运动才警告
    past_3_days_exercise = [(today - timedelta(days=i)) for i in range(3)]
    exercise_records = current_user.exercise_records.filter(
        ExerciseRecord.timestamp >= datetime.combine(today - timedelta(days=2), datetime.min.time()),
        ExerciseRecord.timestamp <= datetime.combine(today, datetime.max.time())
    ).all()
    daily_exercise = {d: 0 for d in past_3_days_exercise}
    for r in exercise_records:
        d = r.timestamp.date()
        if d in daily_exercise:
            daily_exercise[d] += r.duration or 0
    all_days_no_exercise = True
    for d in past_3_days_exercise:
        if daily_exercise[d] > 0:
            all_days_no_exercise = False
            break
    if all_days_no_exercise:
        alert_messages.append(f"警告：你最近三天连续没有运动，建议适当锻炼保持健康！")
    # ========== 预警功能结束 ==========

    return render_template('index.html', title='主页', 
                           general_goal=user_goal, 
                           general_progress=progress_data,
                           exercise_progress_list=exercise_progress_list,
                           alert_messages=alert_messages)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('无效的用户名或密码')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or urlsplit(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', title='登录', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('恭喜，您已成功注册！')
        return redirect(url_for('login'))
    return render_template('register.html', title='注册', form=form)

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.gender = form.gender.data
        current_user.age = form.age.data
        current_user.height = form.height.data
        current_user.weight = form.weight.data
        
        # Calculate and save BMI
        if current_user.height and current_user.weight:
            height_in_meters = current_user.height / 100
            current_user.bmi = round(current_user.weight / (height_in_meters ** 2), 2)
        else:
            current_user.bmi = None
            
        db.session.commit()
        flash('你的个人资料已更新！')
        return redirect(url_for('profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.gender.data = current_user.gender
        form.age.data = current_user.age
        form.height.data = current_user.height
        form.weight.data = current_user.weight
    return render_template('profile.html', title='个人资料', form=form)

@app.route('/goals', methods=['GET', 'POST'])
@login_required
def goals():
    form = GoalForm()
    add_exercise_goal_form = AddExerciseGoalForm()

    # Check which form was submitted by checking the unique submit button's data
    if form.update_general_goals.data and form.validate_on_submit():
        goal = current_user.goal
        if not goal:
            goal = Goal(user_id=current_user.id)
            db.session.add(goal)
        
        goal.target_sleep_hours = form.target_sleep_hours.data
        goal.target_calorie_intake = form.target_calorie_intake.data
        db.session.commit()
        flash('你的通用健康目标已更新！')
        return redirect(url_for('goals'))

    if add_exercise_goal_form.add_exercise_goal.data and add_exercise_goal_form.validate_on_submit():
        new_goal = ExerciseGoal(
            user_id=current_user.id,
            goal_type=add_exercise_goal_form.goal_type.data,
            target_value=add_exercise_goal_form.target_value.data,
            exercise_type=add_exercise_goal_form.exercise_type.data or None
        )
        db.session.add(new_goal)
        db.session.commit()
        flash('新的运动目标已添加！')
        return redirect(url_for('goals'))

    if request.method == 'GET':
        if current_user.goal:
            form.target_sleep_hours.data = current_user.goal.target_sleep_hours
            form.target_calorie_intake.data = current_user.goal.target_calorie_intake
    
    exercise_goals = current_user.exercise_goals.all()
            
    return render_template('goals.html', title='健康目标', form=form, 
                           add_exercise_goal_form=add_exercise_goal_form, 
                           exercise_goals=exercise_goals)

@app.route('/delete_exercise_goal/<int:goal_id>', methods=['POST'])
@login_required
def delete_exercise_goal(goal_id):
    goal = ExerciseGoal.query.get_or_404(goal_id)
    if goal.user_id != current_user.id:
        abort(403)
    db.session.delete(goal)
    db.session.commit()
    flash('运动目标已删除。')
    return redirect(url_for('goals'))


@app.route('/sleep', methods=['GET', 'POST'])
@login_required
def sleep():
    form = SleepForm()
    if form.validate_on_submit():
        try:
            sleep_time_obj = datetime.strptime(form.sleep_time.data, '%Y-%m-%d %H:%M')
            wakeup_time_obj = datetime.strptime(form.wakeup_time.data, '%Y-%m-%d %H:%M')

            if wakeup_time_obj <= sleep_time_obj:
                flash('起床时间必须晚于入睡时间。')
                return redirect(url_for('sleep'))

            overlapping_records = SleepRecord.query.filter(
                SleepRecord.author == current_user,
                SleepRecord.sleep_time < wakeup_time_obj,
                SleepRecord.wakeup_time > sleep_time_obj
            ).first()

            if overlapping_records:
                flash('错误：该时间段与已有的睡眠记录重叠。')
                return redirect(url_for('sleep'))

            duration = (wakeup_time_obj - sleep_time_obj).total_seconds() / 3600
            sleep_record = SleepRecord(
                sleep_time=sleep_time_obj,
                wakeup_time=wakeup_time_obj,
                duration=duration,
                author=current_user
            )
            db.session.add(sleep_record)
            db.session.commit()
            flash('新的睡眠记录已添加！')
            return redirect(url_for('sleep'))
        except ValueError:
            flash('日期格式不正确，请使用 YYYY-MM-DD HH:MM 格式。')
            return redirect(url_for('sleep'))
    
    # GET request logic
    sleep_records = current_user.sleep_records.order_by(SleepRecord.sleep_time.desc()).all()
    today_utc = datetime.utcnow().date()
    monday = today_utc - timedelta(days=today_utc.weekday())
    next_monday = monday + timedelta(days=7)
    last_7_days = [monday + timedelta(days=i) for i in range(0, 7)]
    days_so_far = (today_utc - monday).days + 1
    # 归属日期调整：按醒来的日期归类，筛选所有醒来日期在本周的记录
    sleep_segments = {d: [] for d in last_7_days}
    records_for_plot = current_user.sleep_records.filter(
        SleepRecord.wakeup_time >= datetime.combine(monday, datetime.min.time()),
        SleepRecord.wakeup_time < datetime.combine(next_monday, datetime.min.time())
    ).all()
    for record in records_for_plot:
        st = record.sleep_time
        et = record.wakeup_time
        assign_date = et.date()  # 归属到醒来的那一天
        if assign_date in sleep_segments:
            sleep_segments[assign_date].append({
                'duration': round(record.duration, 2),
                'sleep_time': st.strftime('%H:%M'),
                'wakeup_time': et.strftime('%H:%M')
            })
    # 构造前端数据
    sleep_dates = [d.strftime('%m-%d') for d in last_7_days]
    sleep_durations = [[seg['duration'] for seg in sleep_segments[d]] for d in last_7_days]
    sleep_times = [[seg['sleep_time'] for seg in sleep_segments[d]] for d in last_7_days]
    wakeup_times = [[seg['wakeup_time'] for seg in sleep_segments[d]] for d in last_7_days]
    # 只用已过天数做分母
    avg_sleep = round(sum([sum(day) for day in sleep_durations[:days_so_far]]) / days_so_far, 2) if days_so_far > 0 else 0
    target_sleep_hours = current_user.goal.target_sleep_hours if current_user.goal and current_user.goal.target_sleep_hours else None
    return render_template('sleep.html', title='睡眠', form=form, sleep_records=sleep_records, sleep_dates=sleep_dates, sleep_durations=sleep_durations, avg_sleep=avg_sleep, target_sleep_hours=target_sleep_hours, sleep_times=sleep_times, wakeup_times=wakeup_times)

@app.route('/exercise', methods=['GET', 'POST'])
@login_required
def exercise():
    form = ExerciseForm()
    
    MET_VALUES = {
        '跑步': 7.0,
        '游泳': 8.0,
        '瑜伽': 2.5,
        '骑行': 6.8,
    }
    
    if current_user.weight:
        user_weight_kg = current_user.weight
    else:
        user_weight_kg = 60 # Default weight if not set
        flash('请在“个人资料”页面更新您的体重，以便更精确地计算卡路里消耗。', 'info')

    if form.validate_on_submit():
        exercise_date_str = form.exercise_date.data
        try:
            exercise_date = datetime.strptime(exercise_date_str, '%Y-%m-%d')
        except ValueError:
            flash('日期格式不正确，请使用 YYYY-MM-DD 格式。')
            return redirect(url_for('exercise'))

        exercise_type = form.exercise_type.data
        duration = form.duration.data
        calories_burned = form.calories_burned.data

        if exercise_type == '其它':
            if not calories_burned:
                flash('当运动类型为“其它”时，必须手动填写消耗的卡路里。')
                return redirect(url_for('exercise'))
        else:
            met = MET_VALUES.get(exercise_type, 0)
            calories_burned = (duration * met * 3.5 * user_weight_kg) / 200

        exercise_record = ExerciseRecord(
            exercise_type=exercise_type,
            duration=duration,
            calories_burned=calories_burned,
            timestamp=exercise_date,
            author=current_user
        )
        db.session.add(exercise_record)
        db.session.commit()
        flash('新的运动记录已添加！')
        return redirect(url_for('exercise'))
    
    # 统计最近一周每种运动类型的总时长
    monday = datetime.utcnow().date() - timedelta(days=datetime.utcnow().date().weekday())
    next_monday = monday + timedelta(days=7)
    exercise_records_week = current_user.exercise_records.filter(
        ExerciseRecord.timestamp >= datetime.combine(monday, datetime.min.time()),
        ExerciseRecord.timestamp < datetime.combine(next_monday, datetime.min.time())
    ).all()
    duration_by_type = defaultdict(float)
    for r in exercise_records_week:
        if r.exercise_type:
            duration_by_type[r.exercise_type] += r.duration or 0
    # 转为前端友好格式
    duration_stats = [
        {'type': k, 'duration': round(v, 1)} for k, v in duration_by_type.items()
    ]
    exercise_records = current_user.exercise_records.order_by(ExerciseRecord.timestamp.desc()).all()
    return render_template('exercise.html', title='运动', form=form, exercise_records=exercise_records, duration_stats=duration_stats)

@app.route('/diet', methods=['GET', 'POST'])
@login_required
def diet():
    form = DietForm()

    # Calorie reference values per 100g, hardcoded like in the exercise module
    CALORIES_PER_100G = {
        '米饭': 130, '馒头': 223, '鸡胸肉': 165, '牛肉': 250, 
        '鸡蛋': 155, '牛奶': 54, '苹果': 52, '香蕉': 89, 
        '西兰花': 55, '胡萝卜': 41
    }

    if form.validate_on_submit():
        food_choice = form.food_choice.data
        portion = form.portion.data
        meal_type = form.meal_type.data
        
        food_name = ""
        calories = 0

        if food_choice == '其它':
            food_name = form.other_food_name.data
            calories = form.other_calories.data
            # For 'Other', we consider the entered portion as 1 serving, not in grams
            portion = 1 
            if not food_name or not calories:
                flash('当选择“其它”时，必须手动填写食物名称和总卡路里。')
                return redirect(url_for('diet'))
        else:
            food_name = food_choice
            calories_per_100g = CALORIES_PER_100G.get(food_name, 0)
            calories = (portion / 100) * calories_per_100g

        if calories > 0:
            diet_record = DietRecord(
                food_name=food_name,
                portion=portion,
                calories=calories,
                meal_type=meal_type,
                author=current_user
            )
            db.session.add(diet_record)
            db.session.commit()
            flash('新的饮食记录已添加！')
        else:
            flash('无法计算卡路里，请检查输入。')
        
        return redirect(url_for('diet'))

    monday = datetime.utcnow().date() - timedelta(days=datetime.utcnow().date().weekday())
    next_monday = monday + timedelta(days=7)
    diet_records = current_user.diet_records.filter(
        DietRecord.timestamp >= datetime.combine(monday, datetime.min.time()),
        DietRecord.timestamp < datetime.combine(next_monday, datetime.min.time())
    ).order_by(DietRecord.timestamp.desc()).all()
    return render_template('diet.html', title='饮食', form=form, diet_records=diet_records)

@app.route('/report')
@login_required
def report():
    one_week_ago = datetime.utcnow() - timedelta(days=7)
    sleep_records = current_user.sleep_records.filter(SleepRecord.sleep_time >= one_week_ago).all()
    exercise_records = current_user.exercise_records.filter(ExerciseRecord.timestamp >= one_week_ago).all()
    diet_records = current_user.diet_records.filter(DietRecord.timestamp >= one_week_ago).all()

    total_sleep_hours = sum(r.duration for r in sleep_records)
    avg_sleep = total_sleep_hours / 7 if sleep_records else 0
    
    total_calories_burned = sum(r.calories_burned for r in exercise_records)
    avg_calories_burned = total_calories_burned / 7 if exercise_records else 0
    
    total_calories_eaten = sum(r.calories for r in diet_records)
    avg_calories_eaten = total_calories_eaten / 7 if diet_records else 0
    
    advice_list = []
    if not sleep_records and not exercise_records and not diet_records:
        advice_list.append("你最近一周还没有任何记录，快去添加一些数据来生成你的专属健康报告吧！")
    else:
        if avg_sleep > 0 and avg_sleep < 7:
            advice_list.append("你的周平均睡眠时长似乎不足7小时，请注意保证充足休息。")
        elif avg_sleep > 9:
            advice_list.append("你的周平均睡眠时长超过9小时，如非特殊情况，需警惕睡眠过多。")
        else:
            advice_list.append("你的睡眠状况看起来不错，请保持。")

        calorie_balance = avg_calories_eaten - avg_calories_burned
        if calorie_balance > 300:
            advice_list.append("近期你的日均热量摄入似乎高于消耗，请关注饮食与运动的平衡。")
        elif calorie_balance < -300:
            advice_list.append("近期你的日均热量消耗似乎高于摄入，请确保营养充足以维持体力。")
        else:
            advice_list.append("你的热量摄入与消耗基本平衡，做得很好！")

        if not exercise_records:
            advice_list.append("你最近一周没有运动记录，别忘了适度锻炼是健康的关键哦。")
    
    # Add BMI advice
    bmi_status = None
    if current_user.bmi:
        bmi = current_user.bmi
        if bmi < 18.5:
            bmi_status = "偏瘦"
            advice_list.append(f"你的BMI为 {bmi}，属于偏瘦范围，请注意均衡营养。")
        elif 18.5 <= bmi < 25:
            bmi_status = "正常"
            advice_list.append(f"你的BMI为 {bmi}，属于正常范围，请继续保持！")
        elif 25 <= bmi < 30:
            bmi_status = "超重"
            advice_list.append(f"你的BMI为 {bmi}，属于超重范围，建议通过饮食和运动进行调整。")
        else:
            bmi_status = "肥胖"
            advice_list.append(f"你的BMI为 {bmi}，属于肥胖范围，请关注相关健康风险。")

    # Convert UTC time to Beijing Time (UTC+8)
    report_time_utc = datetime.utcnow()
    report_time_beijing = report_time_utc + timedelta(hours=8)
    
    return render_template('report.html', title='健康报告', 
                           advice_list=advice_list, 
                           avg_sleep=avg_sleep, 
                           avg_calories_burned=avg_calories_burned, 
                           avg_calories_eaten=avg_calories_eaten,
                           bmi_status=bmi_status,
                           report_time=report_time_beijing)

@app.route('/delete_sleep/<int:record_id>', methods=['POST'])
@login_required
def delete_sleep(record_id):
    record = SleepRecord.query.get_or_404(record_id)
    if record.author != current_user:
        abort(403)
    db.session.delete(record)
    db.session.commit()
    flash('睡眠记录已删除！')
    return redirect(url_for('sleep'))

@app.route('/delete_exercise/<int:record_id>', methods=['POST'])
@login_required
def delete_exercise(record_id):
    record = ExerciseRecord.query.get_or_404(record_id)
    if record.author != current_user:
        abort(403)
    db.session.delete(record)
    db.session.commit()
    flash('运动记录已删除！')
    return redirect(url_for('exercise'))

@app.route('/delete_diet/<int:record_id>', methods=['POST'])
@login_required
def delete_diet(record_id):
    record = DietRecord.query.get_or_404(record_id)
    if record.author != current_user:
        abort(403)
    db.session.delete(record)
    db.session.commit()
    flash('饮食记录已删除！')
    return redirect(url_for('diet'))

@app.route('/get_deepseek_advice', methods=['POST'])
@login_required
def get_deepseek_advice():
    one_week_ago = datetime.utcnow() - timedelta(days=7)
    sleep_records = current_user.sleep_records.filter(SleepRecord.sleep_time >= one_week_ago).all()
    exercise_records = current_user.exercise_records.filter(ExerciseRecord.timestamp >= one_week_ago).all()
    diet_records = current_user.diet_records.filter(DietRecord.timestamp >= one_week_ago).all()

    total_sleep_hours = sum(r.duration for r in sleep_records)
    avg_sleep = total_sleep_hours / 7 if sleep_records else 0
    
    total_calories_burned = sum(r.calories_burned for r in exercise_records)
    avg_calories_burned = total_calories_burned / 7 if exercise_records else 0
    
    total_calories_eaten = sum(r.calories for r in diet_records)
    avg_calories_eaten = total_calories_eaten / 7 if diet_records else 0

    prompt = "请根据以下健康数据给出健康评估和建议，数据包含周平均睡眠时长（小时/天）、身体质量指数（BMI）、周日均摄入热量（大卡）和周日均运动消耗（大卡）。并且给出食谱建议。"
    # 构造符合 DeepSeek API 格式的请求数据
    messages = [
        {
            "role": "user",
            "content": f"{prompt} 周平均睡眠时长：{avg_sleep} 小时/天，BMI：{current_user.bmi if current_user.bmi else '无数据'}，周日均摄入热量：{avg_calories_eaten} 大卡，周日均运动消耗：{avg_calories_burned} 大卡"
        }
    ]

    payload = {
        "model": "deepseek-chat",
        "messages": messages,
        "max_tokens": 1000,
        "temperature": 0.3
    }

    # 调用 DeepSeek API
    deepseek_api_key = 'sk-19cca959be3243b89eb3e2f5e986e78b'
    deepseek_advice = None
    if deepseek_api_key:
        headers = {
            "Authorization": f"Bearer {deepseek_api_key}",
            "Content-Type": "application/json"
        }
        try:
            response = requests.post(
                "https://api.deepseek.com/v1/chat/completions",
                json=payload,
                headers=headers
            )
            response.raise_for_status()
            deepseek_response = response.json()
            # 根据 DeepSeek API 返回结构提取建议
            if 'choices' in deepseek_response and deepseek_response['choices']:
                message_content = deepseek_response['choices'][0]['message']['content']
                deepseek_advice = message_content
        except requests.RequestException as e:
            app.logger.error(f"调用 DeepSeek API 出错: {e}")
            deepseek_advice = "无法获取 DeepSeek 的健康评估建议，请稍后重试。"
    else:
        deepseek_advice = "未配置 DeepSeek API 密钥，无法获取额外的健康评估建议。"

    session['deepseek_advice'] = deepseek_advice
    return jsonify({'advice': deepseek_advice})