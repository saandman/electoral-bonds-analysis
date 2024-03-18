import helper
import streamlit as st


st.sidebar.title('The Electoral Bond Analysis')
st.sidebar.markdown('Download the cleaned excel sheet from [here](https://gofile.io/d/zMzapV)')

try:
    df = helper.load_data('donations_cleaned.csv')
    df = helper.donor_preprocess(df)
    banana = helper.banana_preprocess(df)
    encashment = helper.load_data('encashment_cleaned.csv')
except Exception as e:
    st.error(str(e))

name_list = helper.fetch_name_list(df)
selected_name = st.sidebar.selectbox('Select donor', name_list)
columns_to_display = ['purchase_date', 'donor_name', 'amount']

if st.sidebar.button("Show Analysis"):
    if selected_name == "All":
        donor_stats = helper.fetch_all_donation_stats(df)
        st.title(f'Bonds Issued: ₹{donor_stats.total_donation}')
        st.markdown(f"## All Donations")
        
        st.write(df[columns_to_display])

        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"##### Date Range: {donor_stats.start_year} - {donor_stats.end_year}")
            st.markdown(f"##### No. of Donations: {donor_stats.num_donations}")
            st.markdown(f"##### No. of Donors: {donor_stats.num_donors}")
        with col2:
            st.markdown(f"##### Mean/Avg Donation: ₹{donor_stats.mean_donation}")
            st.markdown(f"##### Median Donation: ₹{donor_stats.median_donation}")
            st.markdown(f"##### Most Frequent denomination: ₹{donor_stats.freq_donation_denominations} ({donor_stats.max_freq_donation_count} times)")
            st.markdown(f"##### No. of unique denominations: {donor_stats.unique_donation_denominations}")
        
        st.markdown("## Bananas 🍌 For Scale")
        st.write(banana)

        st.markdown(f"##### League")
        league = helper.fetch_league_table(banana)
        st.write(league)
        st.markdown("""
        * count_percentage - percentage of people out of the whole
        * sum_amount_percentage - percentage of money donated per league out of the whole
        
        Context -
        * upto 1 lakh = 🍌
        * 1 lakh - 50 lakh = 🍌🍌
        * 50 lakh - 1 crore = 🍌🍌🍌
        * 1 crore - 50 crores = 🍌🍌🍌🍌
        * greater than 50 crores = 🍌🍌🍌🍌🍌
        """)

    else:
        st.markdown(f"### {selected_name}")
        temp_df = df[df['donor_name'] == selected_name].copy()
        search_url = helper.fetch_search_url(selected_name)
        st.markdown(f'<a href="{search_url}" target="_blank">Google {selected_name}\'s activities</a>', unsafe_allow_html=True)
        user_stats = helper.fetch_user_donation_stats(selected_name, temp_df, banana)
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"##### Date Range: {user_stats.start_year} - {user_stats.end_year}")
            st.markdown(f"##### League: {user_stats.rating}")
            st.markdown(f"##### No. of Donations: {user_stats.num_donations}")
            st.markdown(f"##### Total Donation: ₹{user_stats.total_donation}")
        with col2:
            st.markdown(f"##### Mean/Avg Donation: ₹{user_stats.mean_donation}")
            st.markdown(f"##### Median Donation: ₹{user_stats.median_donation}")
            st.markdown(f"##### Most Frequent denomination: ₹{user_stats.freq_donation_denominations} ({user_stats.max_freq_donation_count} times)")
        st.write(temp_df[columns_to_display])
        helper.plot_purchase_heatmap(temp_df)
        
        st.write('An approximate list of political parties who encashed bonds during the period of this donor\'s purchase date and the bond\'s validity period (15 days). There\'s no way to know the real benificiaries without the unique numbers -')
        st.write(helper.fetch_bonds_encashed_by_validity_period(temp_df, encashment))
        
    
    if selected_name == "All":
        st.markdown(f"## Party Stats")
        encashment_stats = helper.fetch_encashment_stats(encashment)
        redemptions = helper.redemptions_preprocess(encashment, encashment_stats.total_encashed)
        st.markdown(f"##### Number of Parties: {encashment_stats.num_parties}")
        st.markdown(f"##### Number of times Bonds Encashed: {encashment_stats.num_encashments}")
        st.markdown(f"##### Total Encashed: ₹{encashment_stats.total_encashed}")

        st.write(redemptions)

    if selected_name == "All":
        helper.plot_purchase_encashed_heatmap(df, encashment)
        encashed_minus_issued = donor_stats.total_donation - encashment_stats.total_encashed
        st.markdown(f"""There is a discrepancy of **Rs. {encashed_minus_issued}** in the EB encashed from EB issued data given.""")
        st.markdown(f"""(Graphs not in order, check year)""")
        helper.plot_encashment(df, encashment)
        helper.plot_purchase_vs_encashment(donor_stats.total_donation, encashment_stats.total_encashed)


    if selected_name == "All":
        st.markdown(f"## Wordcloud of Donors")
        wordcloud_image = helper.generate_wordcloud(df)
        st.image(wordcloud_image, use_column_width=True)


st.sidebar.markdown("""---""") 
st.sidebar.markdown("""---""")
st.sidebar.markdown("""---""")
st.sidebar.markdown("""
    Support the developer -
    * UPI - sandman.zip@oksbi
    * [PayPal](https://paypal.me/saandman)
    * [Buy Me A Coffee](https://www.buymeacoffee.com/saandman)
""")
