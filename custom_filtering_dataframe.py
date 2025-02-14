# Custom Functions
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

def _calculate_return_bps(group):
        return (group["Close"].iloc[-1]-group["Open"].iloc[0]) * 16

def get_session_returns(df,name):
        returns = (
            df.groupby(["US/Eastern Timezone"], group_keys=False)
            .apply(_calculate_return_bps, include_groups=False)
            .reset_index()
        )
        returns.columns = ["US/Eastern Timezone",name]
        return returns

def movement(movement_type, df):
    df = df.copy()  # Ensures we don't modify original DataFrame

    if movement_type == 'Up':
        df = df[df[df.columns[-1]] >= 0]

    elif movement_type == 'Down':
        df = df[df[df.columns[-1]] <= 0]
        df.loc[:, df.columns[-1]] = np.where(df[df.columns[-1]] != 0, df[df.columns[-1]] * -1, 0) #creates a copy

    elif movement_type == 'Absolute':
        df.loc[:, df.columns[-1]] = np.abs(df[df.columns[-1]]) #creates a copy

    else:
        raise ValueError("Invalid Movement Type. Choose 'Up', 'Down', or 'Absolute'.")

    return df.reset_index(drop=True)

     
def get_dataframe(interval='1h',ticker_name='ZN',folder='Intraday_data_files'):
    for file in os.scandir(folder):
       if file.is_file():
          if all(x in str(file.name) for x in [interval, ticker_name]) and file.name.endswith('.csv'):
              df=pd.read_csv(os.path.join(folder,file.name))
              print('Mydf:',df)
              break
    return df

def filter_dataframe(pre_df,filter_list="",day_dict="",timezone_column="",target_timezone=""):
    # Filters based on "US/Eastern Timezone" column at the end.
    pre_df[timezone_column] = pd.to_datetime(pre_df.Datetime, errors='coerce')
    pre_df[timezone_column] = pre_df[timezone_column].dt.tz_convert(target_timezone)

    pre_df[f'Day as per {timezone_column}']=pre_df[timezone_column].dt.day_name()
    # Filter day and date
    if filter_list:
        condition=False
        for se in filter_list:
            start=se[0]
            end=se[1]
            day=day_dict[se]
            
            if day in ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']:
                condition=condition | ( (pre_df[pre_df.columns[-2]].dt.hour>=start) & (pre_df[pre_df.columns[-2]].dt.hour<end) & (pre_df[pre_df.columns[-1]]==day))
            
            elif day=="":
                condition=condition | ( (pre_df[pre_df.columns[-2]].dt.hour>=start) & (pre_df[pre_df.columns[-2]].dt.hour<end))
            
        pre_df=pre_df[condition]

    # # Filter event list
    # if event_val!="":
    #     condition=False
    #     event_val=[str(i).lower() for i in event_val]
    #     for event in event_val:
    #         condition|= (pre_df['Event'].str.strip().str.lower().eq(event))
    
    # pre_df=pre_df[condition] 

    return pre_df.reset_index(drop=True)

def calculate_stats_and_plots(df,name,version,check_movement):
    my_df=df.copy()
    # Calculate Session Return close(last entru) - open(first entry)
    returns = get_session_returns(my_df,name)
    returns=movement(version,returns)
    #returns['Session']=returns['Year'].astype(str)+'/'+returns['Month'].astype(str)
    print(f'{name} Session Returns: {returns}')
    
    # Calculate statistics for given scenario
    my_pctiles=[0.1,0.25,0.5,0.75,0.9,0.95,0.99]
    returns_stats=returns[name].describe(percentiles=my_pctiles)
    print(returns_stats)
    current_bps=check_movement
    percentile=(returns[name] <= current_bps).mean() * 100
    percentile=round(percentile,2)
    zscore= (current_bps-returns[name].mean())/returns[name].std()
    zscore=round(zscore,2)
    print(f'Z Score for bps<={current_bps}: {zscore}')
    print(f'Prob bps<={round(current_bps,2)}: {percentile}%ile')
    print(f'Prob bps>{round(current_bps,2)}: {100-percentile}%ile')

    # Plot the return probability along with ZScore
    plt.figure(figsize=(10, 6))
    sns.kdeplot(data=returns, x=f"{name}",cumulative=True,fill=True,color='blue')
    #name=name.replace('Returns','Returns (Close - Open)')
    plt.title(f'{name}', fontdict={'fontsize': 8, 'fontweight': 'bold'})# 'fontname': 'Arial'})
    plt.xlabel('Return')
    plt.ylabel('Cumulative Probability')

    # Set the statistics on the graph
    y_value=percentile/100
    # Restrict the vertical line to stay within the graph
    plt.axvline(x=current_bps, color='red', linestyle='--', label=f'X: {current_bps}')

    # Add a horizontal line at the corresponding probability value
    plt.axhline(y=y_value, xmin=0, xmax=1, color='green', linestyle='--', label=f'P(bps<={current_bps}):{percentile}%')

    # Annotate the intersection point
    plt.annotate(f'(Pr bps<={current_bps}, {percentile:.2f}%ile)',
                xy=(current_bps, y_value),
                xytext=(current_bps + 2, y_value + 0.02),
                color='black',
                arrowprops=dict(facecolor='black', arrowstyle='->'))
    plt.scatter(x=current_bps,y=y_value,color='black',alpha=1)

    percentiles=returns_stats.to_frame()
    percentiles.columns=['bps']
    mean = percentiles.loc['mean', 'bps']
    std = percentiles.loc['std', 'bps']
    perc0 = percentiles.loc['min', 'bps']
    perc10 = percentiles.loc['10%', 'bps']
    perc25 = percentiles.loc['25%', 'bps']
    perc50 = percentiles.loc['50%', 'bps']
    perc75 = percentiles.loc['75%', 'bps']
    perc90 = percentiles.loc['90%', 'bps']
    perc95 = percentiles.loc['95%', 'bps']
    perc99 = percentiles.loc['99%', 'bps']
    perc100 = percentiles.loc['max', 'bps']
    stats_text = f"""Mean: {mean:.2f} bps
                    Std: {std:.1f} bps
                    0%ile (Min): {perc0:.2f} bps
                    10%ile: {perc10:.2f} bps
                    25%ile: {perc25:.2f} bps
                    50%ile (Median): {perc50:.2f} bps
                    75%ile: {perc75:.2f} bps
                    90%ile: {perc90:.1f} bps
                    95%ile: {perc95:.1f} bps
                    99%ile: {perc99:.1f} bps
                    100%ile (Max): {perc100:.2f} bps"""
    plt.text(
            0.95,
            0.75,
            stats_text,
            transform=plt.gca().transAxes,
            verticalalignment="top",
            horizontalalignment="right",
            bbox=dict(
                boxstyle="round",
                facecolor="#FFFFF0",
                edgecolor="#2F4F4F",
                alpha=0.8,
            ),
            color="#000000",
            fontsize=10,
        )
    plt.show()
    custom_dic={}
    for key,val in zip(['df','stats','%<=','%>','zscore<=','plot'],
                       [returns,returns_stats,percentile,100-percentile,zscore,plt]):
        custom_dic[key]=val
    return custom_dic

if __name__=='__main__':
    print(filter_dataframe(get_dataframe(),timezone_column='US/Eastern Timezone',
                                                                    target_timezone='US/Eastern'))