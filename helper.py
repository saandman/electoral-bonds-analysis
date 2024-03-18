import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
from collections import namedtuple
import seaborn as sns
import calendar
from wordcloud import WordCloud
import io


############# Preprocess ################


@st.cache_resource
def load_data(file_path):
    return pd.read_csv(file_path)

def fetch_bond_validity_range(purchase_date):
    validity_date = purchase_date + pd.Timedelta(days=15)
    return validity_date

def donor_preprocess(df):
    df['purchase_date'] = pd.to_datetime(df['purchase_date'])
    df['validity_date'] = df['purchase_date'].apply(fetch_bond_validity_range)
    df['validity_date'] = pd.to_datetime(df['validity_date'])
    return df

def encashment_preprocess(encashment):
    encashment['encashment_date'] = pd.to_datetime(encashment['encashment_date'])
    return encashment

BANANA_EMOJI = {
    '🍌': 100000,
    '🍌🍌': 5000000,
    '🍌🍌🍌': 10000000,
    '🍌🍌🍌🍌': 500000000
}

def banana_rating(total_donation):
    for rating, threshold in BANANA_EMOJI.items():
        if total_donation < threshold:
            return rating
    return '🍌🍌🍌🍌🍌'
    
def banana_preprocess(df):
    banana = df.groupby('donor_name').agg({'amount': 'sum'}).reset_index()
    banana['banana_rating'] = banana['amount'].apply(banana_rating)
    banana = banana.sort_values(by='amount', ascending=False)
    return banana

def redemptions_preprocess(encashment, total_encashed):
    redemptions = encashment.political_party.value_counts()
    encashment_by_party = encashment.groupby('political_party').agg({'amount': 'sum'}).reset_index()
    redemptions = pd.merge(redemptions, encashment_by_party, on='political_party', how='left')
    redemptions.rename(columns={'count': 'count_of_encashments',
                        'amount': 'total_amount'}, inplace=True)
    redemptions['percentage_share'] = (redemptions['total_amount'] / total_encashed) * 100
    return redemptions


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

    DonationStats = namedtuple('Stats', ['num_donations', 'num_donors', 'unique_donation_denominations', 
                                'freq_donation_denominations', 'max_freq_donation_count', 'mean_donation', 'median_donation', 
                                'total_donation', 'start_year', 'end_year',])
    donor_stats = DonationStats(num_donations=num_donations, num_donors=num_donors, unique_donation_denominations=unique_donation_denominations, 
                           freq_donation_denominations=freq_donation_denominations, max_freq_donation_count=max_freq_donation_count, mean_donation=mean_donation,
                           median_donation=median_donation, total_donation=total_donation, start_year=start_year, end_year=end_year)
    return donor_stats


def fetch_user_donation_stats(selected_name, df, banana):
    rating = banana.loc[banana['donor_name'] == selected_name, 'banana_rating'].values[0]
    num_donations = df.shape[0]

    amount_counts = df['amount'].value_counts()
    freq_donation_denominations = amount_counts.idxmax()
    max_freq_donation_count = amount_counts.max()

    mean_donation = df['amount'].mean().round(2)
    median_donation = df['amount'].median().round(2)
    total_donation = df['amount'].sum().round(2)
    start_year = df['purchase_date'].dt.year.min().astype(int)
    end_year = df['purchase_date'].dt.year.max().astype(int)

    UserStats = namedtuple('Stats', ['rating', 'num_donations', 'freq_donation_denominations', 'max_freq_donation_count',
                                 'mean_donation', 'median_donation', 'total_donation', 'start_year', 'end_year',])
    
    user_stats = UserStats(rating=rating, num_donations=num_donations, 
                           freq_donation_denominations=freq_donation_denominations, max_freq_donation_count=max_freq_donation_count,
                           mean_donation=mean_donation, median_donation=median_donation, total_donation=total_donation,
                           start_year=start_year, end_year=end_year)
    return user_stats

def fetch_encashment_stats(encashment):
    num_encashments = encashment.shape[0]
    num_parties = encashment['political_party'].nunique()
    total_encashed = encashment['amount'].sum()

    EncashmentStats = namedtuple('Stats', ['num_encashments', 'num_parties', 'total_encashed'])
    encashment_stats = EncashmentStats(num_encashments=num_encashments, num_parties=num_parties, 
                           total_encashed=total_encashed)
    return encashment_stats

def fetch_league_table(banana):
    league = banana['banana_rating'].value_counts().reset_index(name='count')
    amount_sum = banana.groupby('banana_rating')['amount'].sum().reset_index(name='sum_amount')
    league = pd.merge(league, amount_sum, on='banana_rating')
    total_count = league['count'].sum()
    total_sum_amount = league['sum_amount'].sum()
    league['count_percentage'] = (league['count'] / total_count) * 100
    league['sum_amount_percentage'] = (league['sum_amount'] / total_sum_amount) * 100
    league['count_percentage'] = league['count_percentage']
    league['sum_amount_percentage'] = league['sum_amount_percentage']
    league = league.sort_values(by='banana_rating', key=lambda x: x.astype(str).str.len())
    return league

def fetch_search_url(selected_name):
    # search_url = f"https://www.google.com/search?q={selected_name}+(ED|IT|raid|scam|stocks|Enforcement Directorate|Income Tax)"
    search_url = f"https://www.google.com/search?q={selected_name}"
    return search_url


def fetch_bonds_encashed_by_validity_period(temp_df, encashment):
    filtered_encashments = encashment[
    (encashment['encashment_date'] >= temp_df['purchase_date'].min()) & 
    (encashment['encashment_date'] <= temp_df['validity_date'].max())
    ]
    encashment_count = filtered_encashments['political_party'].value_counts()
    encashment_count = encashment_count.rename('number_of_encashments_in_period')

    return encashment_count


################### Plots ####################


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

def plot_heatmap(df, title, ax, color='YlGnBu'):
    pivot_table = df.pivot_table(index='year', columns='month', aggfunc='size')
    pivot_table.columns = pivot_table.columns.map(lambda x: calendar.month_name[x])
    sns.heatmap(pivot_table, cmap=color, annot=True, fmt='g', cbar=True, ax=ax)
    ax.set_title(title)
    ax.set_xlabel('Month')
    ax.set_ylabel('Year')
    ax.tick_params(axis='x', rotation=45)

@st.cache_resource
def plot_purchase_encashed_heatmap(purchase_df, encashed_df):
    fig, axes = plt.subplots(1, 2, figsize=(20, 8))
    plot_heatmap(purchase_df, 'Electoral Bonds Purchase Heatmap', axes[0], color='Greens')
    plot_heatmap(encashed_df, 'Electoral Bonds Encashment Heatmap', axes[1], color='Reds')
    st.pyplot(plt)

@st.cache_resource
def plot_purchase_heatmap(purchase_df):
    plt.figure(figsize=(12, 8))
    ax = plt.gca()
    plot_heatmap(purchase_df, 'Electoral Bonds Purchase Heatmap', ax, color='Greens')
    st.pyplot(plt)

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

@st.cache_resource
def generate_wordcloud(df):
    text = ' '.join(df['donor_name'])
    text = text.upper()
    wordcloud = WordCloud(width=800, height=400, background_color='white').generate(text)
    img_buffer = io.BytesIO()
    wordcloud.to_image().save(img_buffer, format='PNG')
    return img_buffer.getvalue()