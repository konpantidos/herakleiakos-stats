import streamlit as st
import pandas as pd

# 1. Page Configuration
st.set_page_config(page_title="ΗΡΑΚΛΕΙΑΚΟΣ Tracker", layout="wide")

def check_password():
    st.title("🔒 ΗΡΑΚΛΕΙΑΚΟΣ FC Private Dashboard")
    password = st.text_input("Enter the squad password:", type="password")
    if password == "Hra2014":  
        return True
    elif password:
        st.error("Incorrect password")
    return False

if not check_password():
    st.stop()

# 2. Load the Data
# Using @st.cache_data prevents the app from reloading the Excel file every time you click a button
@st.cache_data
def load_data():
    file_path = 'database.xlsx'
    df_players = pd.read_excel(file_path, sheet_name='players')
    df_matches = pd.read_excel(file_path, sheet_name='matches')
    df_stats = pd.read_excel(file_path, sheet_name='player_match_stats')
    
    # 1. Fix the Red Errors: Fill blank scores with '0-0' and remove accidental spaces
    if 'HT_Score' in df_matches.columns:
        df_matches['HT_Score'] = df_matches['HT_Score'].fillna('0-0').astype(str).str.replace(' ', '')
    if 'FT_Score' in df_matches.columns:
        df_matches['FT_Score'] = df_matches['FT_Score'].fillna('0-0').astype(str).str.replace(' ', '')
        
    # 2. Fix the Blank Table: Force all IDs to match exactly by removing hidden spaces
    df_players['Player_ID'] = df_players['Player_ID'].astype(str).str.strip().str.replace('P0', 'P')
    df_stats['Player_ID'] = df_stats['Player_ID'].astype(str).str.strip().str.replace('P0', 'P')
    df_matches['Match_ID'] = df_matches['Match_ID'].astype(str).str.strip()
    df_stats['Match_ID'] = df_stats['Match_ID'].astype(str).str.strip()
    
    return df_players, df_matches, df_stats

df_players, df_matches, df_stats = load_data()

# 3. Sidebar Menu
st.sidebar.title("Menu")
menu = st.sidebar.radio("Navigation", ["Overview", "Match Logs", "Player Stats", "Half Time - Full Time", "Team Statistics"])

# 4. App Routing
# 4. App Routing
st.title("ΗΡΑΚΛΕΙΑΚΟΣ FC")

if menu == "Overview":
    st.subheader("Welcome to the Tracker")
    st.write(f"**Total Players in Database:** {len(df_players)}")
    st.write(f"**Total Matches Logged:** {len(df_matches)}")
    st.info("Select a view from the sidebar menu.")

elif menu == "Match Logs":
    st.subheader("Match History")
    
    phases = ["All"] + list(df_matches['Phase'].dropna().unique())
    selected_phase = st.selectbox("Filter Matches by Phase", phases)
    
    if selected_phase != "All":
        display_matches = df_matches[df_matches['Phase'] == selected_phase]
    else:
        display_matches = df_matches
        
    st.dataframe(display_matches, use_container_width=True, hide_index=True)

    # Goalscorer Details Dropdown
    st.divider()
    st.subheader("Match Details")
    
    match_list = display_matches['Match_ID'].tolist()
    if match_list:
        selected_match = st.selectbox("Select a Match_ID to view scorers:", match_list)
        match_stats = df_stats[df_stats['Match_ID'] == selected_match]
        match_stats = pd.merge(match_stats, df_players[['Player_ID', 'Full_Name']], on='Player_ID', how='left')
        
        scorers = match_stats[match_stats['Goals'] > 0][['Full_Name', 'Goals']]
        
        if not scorers.empty:
            scorers = scorers.sort_values(by='Goals', ascending=False)
            st.dataframe(scorers, hide_index=True)
        else:
            st.info("No goals recorded for ΗΡΑΚΛΕΙΑΚΟΣ in this match.")

elif menu == "Player Stats":
    st.subheader("Player Statistics")
    
    merged_df = pd.merge(df_stats, df_matches[['Match_ID', 'Phase']], on='Match_ID', how='left')
    merged_df = pd.merge(merged_df, df_players[['Player_ID', 'Full_Name']], on='Player_ID', how='left')
    
    available_phases = [p for p in merged_df['Phase'].unique() if pd.notna(p)]
    phases = ["All Time"] + available_phases
    selected_phase = st.selectbox("Select Competition Phase", phases)
    
    if selected_phase != "All Time":
        filtered_df = merged_df[merged_df['Phase'] == selected_phase]
    else:
        filtered_df = merged_df
        
    player_totals = filtered_df.groupby('Full_Name').agg(
        Apps=('Match_ID', 'count'), 
        Starts=('Start', 'sum'),
        Goals=('Goals', 'sum'),
        Assists=('Assists', 'sum')
    ).reset_index()
    
    player_totals = player_totals.sort_values(by=['Goals', 'Apps'], ascending=[False, False])
    st.dataframe(player_totals, use_container_width=True, hide_index=True)

elif menu == "Half Time - Full Time":
    st.subheader("Half Time & Full Time Analysis")
    
    try:
        played = len(df_matches)
        if played == 0:
            st.warning("No matches logged yet.")
        else:
            # Safely split HT scores
            ht_scores = df_matches['HT_Score'].astype(str).str.split('-', n=1, expand=True)
            ht_scored = pd.to_numeric(ht_scores[0], errors='coerce').fillna(0)
            ht_conceded = pd.to_numeric(ht_scores[1] if ht_scores.shape[1] > 1 else 0, errors='coerce').fillna(0)
            
            # Safely split FT scores
            ft_scores = df_matches['FT_Score'].astype(str).str.split('-', n=1, expand=True)
            ft_scored = pd.to_numeric(ft_scores[0], errors='coerce').fillna(0)
            ft_conceded = pd.to_numeric(ft_scores[1] if ft_scores.shape[1] > 1 else 0, errors='coerce').fillna(0)
            
            # Calculate 2nd Half goals
            sh_scored = ft_scored - ht_scored
            sh_conceded = ft_conceded - ht_conceded
            
            # 1. New Goals By Half Table
            st.write("**Goals by Half**")
            half_stats = {
                'Statistic': [
                    '1st Half Goals Scored', 
                    '1st Half Goals Conceded', 
                    '2nd Half Goals Scored', 
                    '2nd Half Goals Conceded'
                ],
                'Total': [
                    int(ht_scored.sum()), 
                    int(ht_conceded.sum()), 
                    int(sh_scored.sum()), 
                    int(sh_conceded.sum())
                ],
                'Average Per Game': [
                    round(ht_scored.sum() / played, 2),
                    round(ht_conceded.sum() / played, 2),
                    round(sh_scored.sum() / played, 2),
                    round(sh_conceded.sum() / played, 2)
                ]
            }
            st.dataframe(pd.DataFrame(half_stats), hide_index=True, use_container_width=True)
            
            st.divider()
            
            # 2. HT-FT Match Flow Results
            st.write("**Match Flow (HT Result - FT Result)**")
            def get_ht(h, a): return 'Winning' if h > a else ('Losing' if h < a else 'Drawing')
            def get_ft(h, a): return 'Win' if h > a else ('Lose' if h < a else 'Draw')
            
            ht_res = [get_ht(h, a) for h, a in zip(ht_scored, ht_conceded)]
            ft_res = [get_ft(h, a) for h, a in zip(ft_scored, ft_conceded)]
            
            df_matches['HT_FT'] = [f"{h}-{f}" for h, f in zip(ht_res, ft_res)]
            ht_ft_counts = df_matches['HT_FT'].value_counts().reset_index()
            ht_ft_counts.columns = ['Statistic', 'Total']
            ht_ft_counts['Neutral'] = ht_ft_counts['Total'] 
            
            st.dataframe(ht_ft_counts, hide_index=True, use_container_width=True)
            
    except Exception as e:
        st.error(f"Error calculating Half Time stats: {e}")

elif menu == "Team Statistics":
    st.subheader("Overall Team Statistics")
    
    try:
        ft_scores = df_matches['FT_Score'].astype(str).str.split('-', n=1, expand=True)
        df_matches['ft_home'] = pd.to_numeric(ft_scores[0], errors='coerce').fillna(0)
        df_matches['ft_away'] = pd.to_numeric(ft_scores[1] if ft_scores.shape[1] > 1 else 0, errors='coerce').fillna(0)
        
        played = len(df_matches)
        won = len(df_matches[df_matches['Result'] == 'W'])
        lost = len(df_matches[df_matches['Result'] == 'L'])
        
        goals_for = df_matches['ft_home'].sum()
        goals_against = df_matches['ft_away'].sum()
        clean_sheets = len(df_matches[df_matches['ft_away'] == 0]) if played > 0 else 0
        failed_to_score = len(df_matches[df_matches['ft_home'] == 0]) if played > 0 else 0
        
        df_matches['goal_diff'] = df_matches['ft_home'] - df_matches['ft_away']
        df_matches['total_match_goals'] = df_matches['ft_home'] + df_matches['ft_away']
        
        biggest_win = df_matches[df_matches['goal_diff'] > 0]['goal_diff'].max() if won > 0 else 0
        biggest_loss = abs(df_matches[df_matches['goal_diff'] < 0]['goal_diff'].min()) if lost > 0 else 0
        one_goal_wins = len(df_matches[df_matches['goal_diff'] == 1])
        one_goal_losses = len(df_matches[df_matches['goal_diff'] == -1])
        
        most_scored = df_matches['ft_home'].max() if played > 0 else 0
        most_conceded = df_matches['ft_away'].max() if played > 0 else 0
        most_total_goals = df_matches['total_match_goals'].max() if played > 0 else 0
        
        avg_scored = round(goals_for / played, 2) if played > 0 else 0
        avg_conceded = round(goals_against / played, 2) if played > 0 else 0
        mins_per_goal_scored = round((played * 50) / goals_for, 2) if goals_for > 0 else 0
        mins_per_goal_conceded = round((played * 50) / goals_against, 2) if goals_against > 0 else 0

        results = df_matches['Result'].fillna('D').tolist()
        win_streak, unbeaten_streak, winless_streak, lose_streak = 0, 0, 0, 0
        max_w, max_unb, max_winless, max_l = 0, 0, 0, 0
        
        for r in results:
            if r == 'W': win_streak += 1; max_w = max(max_w, win_streak)
            else: win_streak = 0
            if r in ['W', 'D']: unbeaten_streak += 1; max_unb = max(max_unb, unbeaten_streak)
            else: unbeaten_streak = 0
            if r in ['L', 'D']: winless_streak += 1; max_winless = max(max_winless, winless_streak)
            else: winless_streak = 0
            if r == 'L': lose_streak += 1; max_l = max(max_l, lose_streak)
            else: lose_streak = 0

        stats_dict = {
            'Statistic': [
                'Played', 'Lost', 'Won', 'Goals For', 'Goals Against', 'Clean Sheets',
                'Failed To Score', 'Biggest Win (Goals)', 'Biggest Loss (Goals)',
                'Longest Winning Streak', 'Longest Unbeaten Streak', 'Longest Winless Streak',
                'Longest Losing Streak', 'Goals Scored', 'Goals Conceded', 
                'Average Goals Scored Per Game', 'Average Goals Conceded Per Game',
                'Mins Per Goal Scored', 'Mins Per Goal Conceded', 'Penalty Goals Scored', 
                'Penalty Goals Conceded', 'One Goal Wins', 'One Goal Losses',
                'Biggest Winning Margin', 'Biggest Losing Margin', 
                'Most Goals Scored In A Single Match', 'Most Goals Conceded In A Single Match', 
                'Most Total Goals Scored In A Single Match'
            ],
            'Total': [
                played, lost, won, goals_for, goals_against, clean_sheets,
                failed_to_score, biggest_win, biggest_loss,
                max_w, max_unb, max_winless, max_l, goals_for, goals_against,
                avg_scored, avg_conceded, mins_per_goal_scored, mins_per_goal_conceded,
                0, 0, one_goal_wins, one_goal_losses, biggest_win, biggest_loss,
                most_scored, most_conceded, most_total_goals
            ]
        }
        
        df_team_summary = pd.DataFrame(stats_dict)
        df_team_summary['Total'] = df_team_summary['Total'].apply(lambda x: int(x) if pd.notnull(x) and x == int(x) else x)
        
        st.dataframe(df_team_summary, hide_index=True, use_container_width=True)
        
    except Exception as e:
        st.error(f"Error calculating stats: {e}")