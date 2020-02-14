
#clean up and reshape the data from the excel file
import datetime
import pandas as pd
import sys


DATA_FILE = "nba_odds_2019-20.xlsx"

# get the clean data set
# reads in the excel file -- does some cleaning and then returns a dataframe
def get_clean_data():
    #read the file into a dataframe
    df = pd.read_excel(DATA_FILE)
    df = df.drop(columns = ["Rot", "2H", "Open"])

    num_rows = int(df.size/(len(df.columns)))

    #build the clean data frame
    clean_df = pd.DataFrame()
    for i in range(0, num_rows, 2):
        # reformat and build the new rows
        #print("grabing ", i, i+1)

        #convert the two row gmae block into single row for each team
        row_0_dict = convert_row(df.loc[i:i+1], i)
        row_1_dict = convert_row(df.loc[i:i+1], i+1)

        #add the new rows to the dataframe
        if(clean_df.empty):
            #if the frame is empty initialize it first
            clean_df = pd.DataFrame(row_0_dict, index=[0])
            clean_df = clean_df.append(row_1_dict, ignore_index=True)
        else:
            #add both rows to the dictionary
            clean_df = clean_df.append(row_0_dict, ignore_index=True)
            clean_df = clean_df.append(row_1_dict, ignore_index=True)


    #doing some more cleaning
    #add these to account for overtime
    clean_df["OT_PTS"] = clean_df.apply(lambda row: calculate_ot_points(row), axis=1)
    clean_df["OPP_OT_PTS"] = clean_df.apply(lambda row: calculate_opp_ot_points(row), axis=1)
    clean_df["OT"] = clean_df.apply(lambda row: set_ot_flag(row), axis=1)
    #clean up the location
    clean_df["location"] = clean_df.apply(lambda row: clean_location(row), axis=1)
    #clean up the date and convert it to datetime
    clean_df["date"] = clean_df.apply(lambda row: format_date(row), axis=1)

    #send the frame over
    return clean_df

# take in two rows that represent a game
# row number indicates whether to convert the first or the second row
# newly formatted row for the given team
def convert_row(game, row_number):

    if(row_number % 2 == 0): #if the row number is even then the opponent is a row above them
        opp_row_num = row_number + 1
    else:                    # if the row number is odd then the opponent is a row below them
        opp_row_num = row_number - 1

    print(row_number, opp_row_num)
    #grab all the values
    date = game.loc[row_number].Date
    location = game.loc[row_number].VH
    team = game.loc[row_number].Team
    first_qtr_pts = game.loc[row_number, "1st"]
    second_qtr_pts = game.loc[row_number, "2nd"]
    third_qtr_pts = game.loc[row_number, "3rd"]
    fourth_qtr_pts = game.loc[row_number, "4th"]
    final_score = game.loc[row_number].Final
    moneyline = game.loc[row_number].ML

    #grab the values for the opponent
    opp_team = game.loc[opp_row_num].Team
    opp_first_qtr_pts = game.loc[opp_row_num, "1st"]
    opp_second_qtr_pts = game.loc[opp_row_num, "2nd"]
    opp_third_qtr_pts = game.loc[opp_row_num, "3rd"]
    opp_fourth_qtr_pts = game.loc[opp_row_num, "4th"]
    opp_final_score = game.loc[opp_row_num].Final
    opp_moneyline = game.loc[opp_row_num].ML

    # grab the total the spread for the game
    # the number for the spread and the total arent always the same
    # in this data assuming the the total will be biger than the spread
    row_0_num = game.loc[row_number].Close
    row_1_num = game.loc[opp_row_num].Close

    #figure out which is the total and which is the spread and put it in a dictionary
    lines = convert_lines(row_0_num, row_1_num)

    #throw everything into a dictionary to add to the dataframe
    return {
        "date": date,
        "location": location,
        "team": team,
        "opp_team": opp_team,
        "1Q_PTS": first_qtr_pts,
        "2Q_PTS": second_qtr_pts,
        "3Q_PTS": third_qtr_pts,
        "4Q_PTS": fourth_qtr_pts,
        "final_score": final_score,
        "opp_1Q_PTS": opp_first_qtr_pts,
        "opp_2Q_PTS": opp_second_qtr_pts,
        "opp_3Q_PTS": opp_third_qtr_pts,
        "opp_4Q_PTS": opp_fourth_qtr_pts,
        "opp_final_score": opp_final_score,
        "moneyline": moneyline,
        "opp_moneyline": opp_moneyline,
        "total": lines["total"],
        "spread": lines["spread"],
    }

#format the date to a datetime object
# takes in the number from the dataset
# returns a datetime object
def format_date(row):
#####set the year for season being handled -- THIS WILL NEED TO BE CHANGED TO HANDLE DATA FROM DIFF SEASONS#####
    start_season = 2019
    end_season = 2020

    #grab the month and the day from the number
    print(row)
    date = row["date"]
    month = int(date/100)
    day = int(date % 100)

    if(month >= 10): #10 is the cutoff because thats when the first game of the season was
        year = 2019
    else:
        year = 2020

    return datetime.date(year, month, day)

def convert_lines(row_0_num, row_1_num):
    PICK_EM_SPREAD = 0.5

    if(type(row_0_num) == str):
        total = row_1_num
        spread = PICK_EM_SPREAD
    elif(type(row_1_num) == str):
        total = row_0_num
        spread = PICK_EM_SPREAD
    else:
        if(row_0_num > row_1_num):
            total = row_0_num
            spread = row_1_num
        else:
            total = row_1_num
            spread = row_0_num


    return {"total": total,
            "spread": spread}


# calculate the points scored in overtime
# if there was no overtime it returns 0
def calculate_ot_points(row):
    total_points = sum(row[["1Q_PTS", "2Q_PTS", "3Q_PTS", "4Q_PTS"]])
    return row.final_score - total_points

# calculate the points the opponent scored in overtime
# if there was no overtime it returns 0
def calculate_opp_ot_points(row):
    total_points = sum(row[["opp_1Q_PTS", "opp_2Q_PTS", "opp_3Q_PTS", "opp_4Q_PTS"]])
    return row.opp_final_score - total_points

#sets the flag for the overtime column
def set_ot_flag(row):
    team_pts = sum(row[["1Q_PTS", "2Q_PTS", "3Q_PTS", "4Q_PTS"]])
    opp_team_pts = sum(row[["opp_1Q_PTS", "opp_2Q_PTS", "opp_3Q_PTS", "opp_4Q_PTS"]])

    if(team_pts == opp_team_pts):
        return 1
    return 0

#clean up the location column
def clean_location(row):
    location = row.location
    if(location == 'V'):
        location = 'A'

    return location
