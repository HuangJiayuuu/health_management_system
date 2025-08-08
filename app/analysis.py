import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score
import matplotlib.pyplot as plt
import io
import base64
from datetime import datetime, timedelta
import matplotlib
from .models import SleepRecord

plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

matplotlib.use('Agg')  # Use non-interactive backend

def generate_sleep_prediction(sleep_records, days_to_predict=7):
    """
    Generate sleep quality prediction using linear regression.
    
    Args:
        sleep_records: List of SleepRecord objects
        days_to_predict: Number of days to predict into the future
        
    Returns:
        dict: Dictionary containing prediction results and visualization
    """
    if len(sleep_records) < 5:
        return {
            'success': False,
            'message': '需要至少5条睡眠记录来生成预测',
            'plot': None,
            'prediction': None,
            'r2_score': None
        }
    
    # Extract data and sort by date
    data = [(record.sleep_time.date(), record.duration) for record in sleep_records]
    data.sort(key=lambda x: x[0])
    
    # Convert to DataFrame
    df = pd.DataFrame(data, columns=['date', 'duration'])
    
    # Create feature (days since first record)
    first_date = df['date'].min()
    df['days_since_start'] = df['date'].apply(lambda x: (x - first_date).days)
    
    # Prepare data for linear regression
    X = df[['days_since_start']].values
    y = df['duration'].values
    
    # Create and train the model
    model = LinearRegression()
    model.fit(X, y)
    
    # Make predictions for historical data
    y_pred = model.predict(X)
    
    # Calculate metrics
    mse = mean_squared_error(y, y_pred)
    r2 = r2_score(y, y_pred)
    
    # Predict future values
    last_day = df['days_since_start'].max()
    future_days = np.array([[last_day + i + 1] for i in range(days_to_predict)])
    future_predictions = model.predict(future_days)
    
    # Generate dates for future predictions
    last_date = df['date'].max()
    future_dates = [last_date + timedelta(days=i+1) for i in range(days_to_predict)]
    
    # Create visualization
    plt.figure(figsize=(10, 6))
    plt.scatter(df['date'], df['duration'], color='blue', label='实际睡眠时长')
    
    # Plot regression line for historical data
    all_days = np.array([[i] for i in range(df['days_since_start'].min(), last_day + days_to_predict + 1)])
    all_predictions = model.predict(all_days)
    all_dates = [first_date + timedelta(days=i) for i in range(len(all_days))]
    plt.plot(all_dates, all_predictions, color='red', label='趋势线')
    
    # Plot future predictions
    plt.scatter(future_dates, future_predictions, color='green', label='预测睡眠时长')
    
    plt.xlabel('日期')
    plt.ylabel('睡眠时长 (小时)')
    plt.title('睡眠时长趋势与预测')
    plt.legend()
    plt.grid(True)
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    # Convert plot to base64 string
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    plot_url = base64.b64encode(img.getvalue()).decode('utf-8')
    plt.close()
    
    return {
        'success': True,
        'message': '预测成功',
        'plot': plot_url,
        'prediction': future_predictions.tolist(),
        'prediction_dates': [date.strftime('%Y-%m-%d') for date in future_dates],
        'r2_score': r2,
        'slope': model.coef_[0]
    }

def analyze_exercise_sleep_correlation(exercise_records, sleep_records):
    """
    Analyze correlation between exercise duration and sleep quality.
    
    Args:
        exercise_records: List of ExerciseRecord objects
        sleep_records: List of SleepRecord objects
        
    Returns:
        dict: Dictionary containing correlation results and visualization
    """
    if len(exercise_records) < 5 or len(sleep_records) < 5:
        return {
            'success': False,
            'message': '需要至少5条运动记录和5条睡眠记录来分析相关性',
            'plot': None,
            'correlation': None
        }
    
    # Create DataFrames
    exercise_df = pd.DataFrame([
        {'date': record.timestamp.date(), 'duration': record.duration}
        for record in exercise_records
    ])
    
    sleep_df = pd.DataFrame([
        {'date': record.sleep_time.date(), 'duration': record.duration}
        for record in sleep_records
    ])
    
    # Group by date and sum exercise duration
    exercise_df = exercise_df.groupby('date')['duration'].sum().reset_index()
    
    # Merge data on date
    merged_df = pd.merge(exercise_df, sleep_df, on='date', how='inner', suffixes=('_exercise', '_sleep'))
    
    if len(merged_df) < 5:
        return {
            'success': False,
            'message': '没有足够的匹配数据来分析相关性（需要至少5天同时有运动和睡眠记录）',
            'plot': None,
            'correlation': None
        }
    
    # Calculate correlation
    correlation = merged_df['duration_exercise'].corr(merged_df['duration_sleep'])
    
    # Create visualization
    plt.figure(figsize=(10, 6))
    plt.scatter(merged_df['duration_exercise'], merged_df['duration_sleep'])
    
    # Add regression line
    X = merged_df[['duration_exercise']].values
    y = merged_df['duration_sleep'].values
    model = LinearRegression()
    model.fit(X, y)
    y_pred = model.predict(X)
    plt.plot(merged_df['duration_exercise'], y_pred, color='red')
    
    plt.xlabel('运动时长 (分钟)')
    plt.ylabel('睡眠时长 (小时)')
    plt.title('运动时长与睡眠质量相关性分析')
    plt.grid(True)
    plt.tight_layout()
    
    # Convert plot to base64 string
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    plot_url = base64.b64encode(img.getvalue()).decode('utf-8')
    plt.close()
    
    # Prepare interpretation
    if correlation > 0.7:
        interpretation = "强正相关：运动时间越长，睡眠时间越长"
    elif correlation > 0.3:
        interpretation = "中等正相关：运动时间越长，睡眠时间有所增加"
    elif correlation > 0:
        interpretation = "弱正相关：运动时间与睡眠时间有轻微正相关"
    elif correlation > -0.3:
        interpretation = "弱负相关：运动时间与睡眠时间有轻微负相关"
    elif correlation > -0.7:
        interpretation = "中等负相关：运动时间越长，睡眠时间有所减少"
    else:
        interpretation = "强负相关：运动时间越长，睡眠时间越短"
    
    return {
        'success': True,
        'message': '分析成功',
        'plot': plot_url,
        'correlation': correlation,
        'interpretation': interpretation,
        'slope': model.coef_[0],
        'data_points': len(merged_df)
    }

def get_weekly_avg_sleep(user):
    """
    计算本周（周一到今天）平均睡眠时长（小时）。
    :param user: User对象
    :return: float, 平均睡眠时长，保留两位小数
    """
    from datetime import datetime, timedelta
    today = datetime.utcnow().date()
    monday = today - timedelta(days=today.weekday())
    days_so_far = (today - monday).days + 1
    # 只统计醒来日期在本周的记录
    sleep_records = user.sleep_records.filter(
        SleepRecord.wakeup_time >= datetime.combine(monday, datetime.min.time()),
        SleepRecord.wakeup_time < datetime.combine(today + timedelta(days=1), datetime.min.time())
    ).all()
    # 归属到醒来的那一天
    sleep_segments = {monday + timedelta(days=i): [] for i in range(days_so_far)}
    for record in sleep_records:
        assign_date = record.wakeup_time.date()
        if assign_date in sleep_segments:
            sleep_segments[assign_date].append(record.duration)
    # 计算每天总时长
    daily_totals = [sum(sleep_segments[d]) for d in sleep_segments]
    avg_sleep = round(sum(daily_totals) / days_so_far, 2) if days_so_far > 0 else 0
    return avg_sleep