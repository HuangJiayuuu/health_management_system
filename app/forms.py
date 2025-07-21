from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, FloatField, SelectField, IntegerField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError, Optional, NumberRange
from app.models import User, FoodItem

class LoginForm(FlaskForm):
    username = StringField('用户名', validators=[DataRequired()])
    password = PasswordField('密码', validators=[DataRequired()])
    remember_me = BooleanField('记住我')
    submit = SubmitField('登录')

class RegistrationForm(FlaskForm):
    username = StringField('用户名', validators=[DataRequired()])
    email = StringField('电子邮箱', validators=[DataRequired(), Email()])
    password = PasswordField('密码', validators=[DataRequired()])
    password2 = PasswordField(
        '重复密码', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('注册')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('用户名已被使用。')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('电子邮箱已被注册。')

class EditProfileForm(FlaskForm):
    username = StringField('用户名', validators=[DataRequired()])
    gender = SelectField('性别', choices=[('', '请选择...'), ('男', '男'), ('女', '女')], validators=[Optional()])
    age = IntegerField('年龄', validators=[Optional()])
    height = FloatField('身高 (cm)', validators=[Optional()])
    weight = FloatField('体重 (kg)', validators=[Optional()])
    submit = SubmitField('保存更改')

class GoalForm(FlaskForm):
    target_sleep_hours = FloatField('每日平均睡眠目标 (小时)', validators=[Optional(), NumberRange(min=0, max=24)])
    target_exercise_minutes = IntegerField('每周总运动目标 (分钟)', validators=[Optional(), NumberRange(min=0)])
    target_calorie_intake = IntegerField('每日平均热量摄入目标 (大卡)', validators=[Optional(), NumberRange(min=0)])
    update_general_goals = SubmitField('设定/更新目标')

class AddExerciseGoalForm(FlaskForm):
    goal_type = SelectField('目标类型',
                            choices=[
                                ('duration', '周运动总时长 (分钟)'),
                                ('frequency', '周运动次数'),
                                ('calories', '周消耗总热量 (大卡)'),
                                # ('distance', '跑步总距离 (公里)') # Can be added later
                            ],
                            validators=[DataRequired()],
                            id='goal_type_select') # Add id for JS
    target_value = FloatField('目标值', validators=[DataRequired(), NumberRange(min=0)])
    exercise_type = SelectField('特定运动 (时长/次数目标)',
                                choices=[
                                    ('', '任何运动'),
                                    ('跑步', '跑步'),
                                    ('游泳', '游泳'),
                                    ('瑜伽', '瑜伽'),
                                    ('骑行', '骑行')
                                ],
                                validators=[Optional()])
    add_exercise_goal = SubmitField('添加运动目标')


class SleepForm(FlaskForm):
    sleep_time = StringField('入睡时间', validators=[DataRequired()])
    wakeup_time = StringField('起床时间', validators=[DataRequired()])
    submit = SubmitField('提交')

class ExerciseForm(FlaskForm):
    exercise_date = StringField('运动日期', validators=[DataRequired()])
    exercise_type = SelectField('运动类型', 
                                choices=[
                                    ('跑步', '跑步 (中等强度)'),
                                    ('游泳', '游泳 (中等强度)'),
                                    ('瑜伽', '瑜伽'),
                                    ('骑行', '骑行 (中等强度)'),
                                    ('其它', '其它')
                                ], 
                                validators=[DataRequired()])
    duration = SelectField('运动时长', 
                           choices=[
                               ('15', '15 分钟'),
                               ('30', '30 分钟'),
                               ('45', '45 分钟'),
                               ('60', '60 分钟'),
                               ('90', '90 分钟')
                           ], 
                           validators=[DataRequired()], coerce=int)
    calories_burned = FloatField('消耗卡路里 (仅当选择“其它”时填写)', validators=[Optional()])
    submit = SubmitField('提交')

class DietForm(FlaskForm):
    food_choice = SelectField('选择食物',
                              choices=[
                                  ('米饭', '米饭'),
                                  ('馒头', '馒头'),
                                  ('鸡胸肉', '鸡胸肉'),
                                  ('牛肉', '牛肉'),
                                  ('鸡蛋', '鸡蛋'),
                                  ('牛奶', '牛奶'),
                                  ('苹果', '苹果'),
                                  ('香蕉', '香蕉'),
                                  ('西兰花', '西兰花'),
                                  ('胡萝卜', '胡萝卜'),
                                  ('其它', '其它')
                              ],
                              validators=[DataRequired()])
    portion = SelectField('份量', 
                          choices=[
                              ('100', '100克 (常规份)'),
                              ('150', '150克'),
                              ('200', '200克 (大份)'),
                              ('50', '50克 (小份)')
                          ],
                          validators=[DataRequired()], coerce=int)
    
    # Fields for 'Other' option
    other_food_name = StringField('食物名称 (当选择“其它”时)', validators=[Optional()])
    other_calories = FloatField('总卡路里 (当选择“其它”时)', validators=[Optional()])

    meal_type = SelectField('餐类型', choices=[('早餐', '早餐'), ('午餐', '午餐'), ('晚餐', '晚餐'), ('加餐', '加餐')], validators=[DataRequired()])
    submit = SubmitField('提交')
