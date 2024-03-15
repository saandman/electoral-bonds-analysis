import pandas as pd
import numpy as np
import streamlit as st
import matplotlib.pyplot as plt
from collections import namedtuple
from num2words import num2words
import seaborn as sns
import calendar
from wordcloud import WordCloud
import io
import re


############# Preprocess ################

def clean_date(date_str):
    try:
        return pd.to_datetime(date_str, format="%d/%b/%Y")
    except Exception as e:
        return pd.NaT

def clean_amount(amount):
    try:
        if isinstance(amount, str):
            amount = amount.replace(',', '').replace(' ', '')
            amount = np.int64(amount)
            return amount
    except (ValueError, OverflowError):
        return np.nan

def clean_name(name):
    try:
        cleaned_name = re.sub(r'\s+', ' ', name).strip()
        return cleaned_name
    except Exception as e:
        return np.nan

def banana_rating(total_donation):
    if total_donation < 100000:
        return '🍌'
    elif 100000 <= total_donation < 5000000:
        return '🍌🍌'
    elif 5000000 <= total_donation < 10000000:
        return '🍌🍌🍌'
    elif 10000000 <= total_donation < 500000000:
        return '🍌🍌🍌🍌'
    else:
        return '🍌🍌🍌🍌🍌'
    

def donation_preprocess(df):
    df.rename(columns={'Date of Purchase': 'purchase_date',
                        'Purchaser Name': 'donor_name',
                        'Denomination': 'amount'}, inplace=True)
    df.dropna(how='all', inplace=True, ignore_index=True)
    df['purchase_date'] = df['purchase_date'].apply(clean_date)
    df['amount'] = df['amount'].apply(clean_amount)
    df['donor_name'] = df['donor_name'].apply(clean_name)
    df['year'] = df['purchase_date'].dt.year
    df['year'] = df['year'].astype(int)
    df['month'] = df['purchase_date'].dt.month

    banana = df.groupby('donor_name').agg({'amount': 'sum'}).reset_index()
    banana['banana_rating'] = banana['amount'].apply(banana_rating)
    banana = banana.sort_values(by='amount', ascending=False)

    return df, banana

def encashment_preprocess(encashment):
    encashment.rename(columns={'Date of\nEncashment': 'encashment_date',
                        'Name of the Political Party': 'political_party',
                        'Denomination': 'amount'}, inplace=True)
    encashment.dropna(how='all', inplace=True, ignore_index=True)
    encashment['encashment_date'] = encashment['encashment_date'].apply(clean_date)
    encashment['amount'] = encashment['amount'].apply(clean_amount)
    encashment['political_party'] = encashment['political_party'].apply(clean_name)
    encashment['year'] = encashment['encashment_date'].dt.year
    encashment['year'] = encashment['year'].astype(int)
    encashment['month'] = encashment['encashment_date'].dt.month


    redemptions = encashment.political_party.value_counts()
    encashment_by_party = encashment.groupby('political_party').agg({'amount': 'sum'}).reset_index()
    redemptions = pd.merge(redemptions, encashment_by_party, on='political_party', how='left')
    redemptions.rename(columns={'count': 'count_of_encashments',
                        'amount': 'total_amount'}, inplace=True)
    total_amount = encashment['amount'].sum()
    redemptions['percentage_share'] = (redemptions['total_amount'] / total_amount) * 100

    return encashment, redemptions

################### Helper functions ####################

def fetch_name_list(df):
    name_list = df['donor_name'].unique().tolist()
    name_list.sort()
    name_list.insert(0,"All")
    return name_list

def fetch_all_donation_stats(df):
    num_donations = df.shape[0]
    num_donors = df['donor_name'].nunique()
    donations_denominations = df['amount'].unique()
    unique_donation_denominations = f"{len(donations_denominations)} - {donations_denominations}"
    
    amount_counts = df['amount'].value_counts()
    freq_donation_denominations = amount_counts.idxmax()
    max_freq_donation_count = amount_counts.max()
    
    mean_donation = df['amount'].mean().round(2)
    median_donation = df['amount'].median().round(2)
    total_donation = df['amount'].sum().round(2)
    
    start_year = df['purchase_date'].dt.year.min().astype(int)
    end_year = df['purchase_date'].dt.year.max().astype(int)

    DonationStats = namedtuple('DonationStats', ['num_donations', 'num_donors', 'unique_donation_denominations', 
                                                 'freq_donation_denominations', 'max_freq_donation_count', 
                                                 'mean_donation', 'median_donation', 'total_donation', 
                                                 'start_year', 'end_year'])
    stats_instance = DonationStats(num_donations, num_donors, unique_donation_denominations, 
                                    freq_donation_denominations, max_freq_donation_count, mean_donation, 
                                    median_donation, total_donation, start_year, end_year)
    return stats_instance

def fetch_user_donation_stats(selected_name, df, banana):
    rating = banana.loc[banana['donor_name'] == selected_name, 'banana_rating'].values[0]
    num_donations = df.shape[0]
    freq_donation_denominations = df['amount'].mode().iloc[0]
    mean_donation = df['amount'].mean().round(2)
    median_donation = df['amount'].median().round(2)
    total_donation = df['amount'].sum().round(2)
    start_year = df['purchase_date'].dt.year.min().astype(int)
    end_year = df['purchase_date'].dt.year.max().astype(int)

    Stats = namedtuple('Stats', ['rating', 'num_donations', 'freq_donation_denominations', 
                                 'mean_donation', 'median_donation', 'total_donation', 'start_year', 'end_year',])
    
    stats_instance = Stats(rating=rating, num_donations=num_donations, 
                           freq_donation_denominations=freq_donation_denominations, mean_donation=mean_donation,
                           median_donation=median_donation, total_donation=total_donation,
                           start_year=start_year, end_year=end_year)
    return stats_instance


def fetch_encashment_stats(encashment):
    num_encashments = encashment.shape[0]
    num_parties = len(encashment['political_party'].unique())
    total_encashed = encashment['amount'].sum().round(2)

    Stats = namedtuple('Stats', ['num_encashments', 'num_parties', 'total_encashed'])
    stats_instance = Stats(num_encashments=num_encashments, num_parties=num_parties, 
                           total_encashed=total_encashed)
    return stats_instance

def get_league_table(banana):
    league = banana['banana_rating'].value_counts().reset_index(name='count')
    amount_sum = banana.groupby('banana_rating')['amount'].sum().reset_index(name='sum_amount')
    league = pd.merge(league, amount_sum, on='banana_rating')
    total_count = league['count'].sum()
    total_sum_amount = league['sum_amount'].sum()
    league['count_percentage'] = (league['count'] / total_count) * 100
    league['sum_amount_percentage'] = (league['sum_amount'] / total_sum_amount) * 100
    league['count_percentage'] = league['count_percentage']
    league['sum_amount_percentage'] = league['sum_amount_percentage']
    # league = league.sort_values(by='banana_rating', key=lambda x: x.str.len())
    league = league.sort_values(by='banana_rating', key=lambda x: x.astype(str).str.len())

    return league

@st.cache_resource
def plot_encashment(df, encashment):
    df_grouped = df.groupby(['year', 'month'])['amount'].sum().reset_index()
    encashment_grouped = encashment.groupby(['year', 'month'])['amount'].sum().reset_index()

    df_grouped = df_grouped.sort_values(['year', 'month'])
    encashment_grouped = encashment_grouped.sort_values(['year', 'month'])

    years = df['year'].unique()

    fig, axes = plt.subplots(nrows=len(years), ncols=1, figsize=(10, 6 * len(years)))

    for i, year in enumerate(years):
        df_year = df_grouped[df_grouped['year'] == year]
        encashment_year = encashment_grouped[encashment_grouped['year'] == year]

        merged_df = pd.merge(df_year, encashment_year, on='month', suffixes=('_purchase', '_encashed'), how='outer')

        axes[i].bar(merged_df['month'], merged_df['amount_purchase'], color='green', width=0.4, label='EB Issued')
        axes[i].bar(merged_df['month'] + 0.4, merged_df['amount_encashed'], color='red', width=0.4, label='EB Encashed')
        axes[i].set_xlabel('Month')
        axes[i].set_ylabel('Amount')
        axes[i].set_title(f'Year {year}: EB Issued vs. EB Encashed')
        axes[i].set_xticks(range(1, 13))
        axes[i].set_xticklabels(['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'])
        axes[i].legend()
        axes[i].ticklabel_format(style='plain', axis='y')

    plt.tight_layout()
    st.pyplot(fig)

def plot_date_volume(df):
    df['purchase_date'] = pd.to_datetime(df['purchase_date'])
    df['day'] = df['purchase_date'].dt.day
    plt.figure(figsize=(12, 6))
    sns.countplot(x=df['day'], data=df.sort_values('purchase_date'))
    plt.title('Distribution of Volume of Transaction by Date Over Time')
    plt.xlabel('Day of the month')
    plt.ylabel('Transaction Count')
    st.pyplot(plt)

def plot_heatmap(df, title, ax, color='YlGnBu'):
    pivot_table = df.pivot_table(index='year', columns='month', aggfunc='size')
    # month no. to names
    pivot_table.columns = pivot_table.columns.map(lambda x: calendar.month_name[x])
    
    sns.heatmap(pivot_table, cmap=color, annot=True, fmt='g', cbar=True, ax=ax)
    ax.set_title(title)
    ax.set_xlabel('Month')
    ax.set_ylabel('Year')
    ax.tick_params(axis='x', rotation=45)

def plot_purchase_encashed_heatmaps(purchase_df, encashed_df):
    fig, axes = plt.subplots(1, 2, figsize=(20, 8))
    plot_heatmap(purchase_df, 'Electoral Bonds Purchase Heatmap', axes[0], color='Greens')
    plot_heatmap(encashed_df, 'Electoral Bonds Encashment Heatmap', axes[1], color='Reds')
    st.pyplot(plt)

def plot_purchase_heatmap(purchase_df):
    plt.figure(figsize=(12, 8))
    ax = plt.gca()
    plot_heatmap(purchase_df, 'Electoral Bonds Purchase Heatmap', ax, color='Greens')
    st.pyplot(plt)


def convert_to_indian_currency(number):
    return num2words(number, lang='en_IN')

def get_search_url(selected_name):
    search_url = f"https://www.google.com/search?q={selected_name}+(ED|IT|raid|scam|stocks|Enforcement Directorate|Income Tax)"
    return search_url


@st.cache_resource
def generate_wordcloud(df):
    text = ' '.join(df['donor_name'])
    text = text.upper()
    wordcloud = WordCloud(width=800, height=400, background_color='white').generate(text)
    
    # Save wordcloud to a BytesIO object
    img_buffer = io.BytesIO()
    wordcloud.to_image().save(img_buffer, format='PNG')
    
    return img_buffer.getvalue()


@st.cache_resource
def plot_purchase_vs_encashment(donated, encashed):
    plt.figure(figsize=(8, 6))
    numbers = [donated, encashed]
    plt.bar(range(len(numbers)), numbers, color=['green', 'red'])
    plt.xticks(range(len(numbers)), ['EB Issued', 'EB Encashed'])
    plt.ylabel('Rupees')
    plt.title('In Summary')
    plt.ticklabel_format(style='plain', axis='y')
    
    st.pyplot(plt)
