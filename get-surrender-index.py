import nflgame
import numpy as np

def get_field_position(play):
    """
    Gets the field position of the play.
    
    Arg: play is the play being analyzed.
    Returns: the field position as an int from 1-100. 
    1-50 represents own half, 50-100 represents opponent half.
    """
    
    if(play.data['yrdln'] == '50'):
        return 50
    
    team_side = play.data['yrdln'].split()[0]
    yard_line = int(play.data['yrdln'].split()[1])
    pos_team = play.data['posteam']
    
    if(pos_team != team_side):
        return (50 + (50 - yard_line))
    
    else:
        return yard_line

def get_first_down_distance(play):
    """
    Gets the first down distance required of the play.
    Arg: play: a Play object
    Returns: First down distance as an int.
    """
    return play.data['ydstogo']

def score_differential(play):
    """
    Gets the score differential for the team in possesion at
    the time of the play.
    Arg: play: a Play object
    Returns: Score differential as an int (from perspective of possession team)
    """
    
    # Identify home team and away team
    home_team = play.drive.game.home
    away_team = play.drive.game.away
    
    # Identify team in possession
    pos_team = play.data['posteam']
    
    # Score is the score list. score[0] is away, score[1] is home
    score = score_at_play(play)
    
    # Calculate score difference from perspective of possession team
    if(pos_team == home_team):
        diff = score[1] - score[0]
    else:
        diff = score[0] - score[1]
        
    return diff

def clock_multiplier(play):
    """
    Gets multiplier to apply to surrender index at the time of the play.
    Arg: play: Play object.
    Returns: float multiplier.
    """
    # Clock: Applies if losing/tied after halftime = ((x*0.001)^3) + 1 for each passing second after halftime
    # Need to account for overtime as well.
    if(play.data['qtr'] == 3):
        # past halftime, 3rd quarter
        time = seconds(play) # Seconds counts how many seconds are in the clock
        
    elif(play.data['qtr'] == 4):
        # past halftime, 4th quarter
        # Calculations must add +15 min worth of seconds to this total
        time = seconds(play) + (15 * 60)
        
    else:
        return 1
        
    multiplier = ((time * 0.001) ** 3) + 1
    return multiplier

def seconds(play):
    """
    Counts how many seconds are left on the clock at the time of a play.
    Arg: play: Play object.
    Returns: int of number of seconds.
    """
    # Gather time string list
    time_str = play.data['time'].split(":")
    time_str[0] = int(time_str[0])
    time_str[1] = int(time_str[1])
    
    time = (60 * time_str[0]) + time_str[1]
    return time

def yard_line_multiplier(play):
    """
    Converts yard line in the form of 1-100 
    Field Position: At or inside 40, base score = 1 + 10% per yard past 40 to 50, + 20% per yard past 50
    Arg: play: Play object
    Returns: float to be used as multiplier
    """
    field_pos = get_field_position(play)
    multiplier = 1
    
    if(field_pos <= 40):
        return 1
    
    elif(field_pos >= 41 and field_pos <= 50):
        numloops = field_pos - 40
        for i in range(numloops):
            multiplier = multiplier * 1.1
        
    elif(field_pos > 50):
        numloops = field_pos - 50
        for i in range(10):
            multiplier = multiplier * 1.1
        for j in range(numloops):
            multiplier = multiplier * 1.2

    return multiplier

def first_down_distance_multiplier(play):
    """
    Converts the first down distance to the appropriate multiplier
    First Down Distance: 4th and 1 = no discount, 4th and 2-3 = 20% off, 4th and 4-6 = 40% off,
                         4th and 7-9 = 60% off, 4th and 10+ = 80% off
    Arg: play: Play object
    Returns: float to be used as multiplier
    """
    multiplier = get_first_down_distance(play)
    
    if(multiplier <= 1):
        return 1
    elif(multiplier == 2 or multiplier == 3):
        return 0.8
    elif(multiplier >= 4 and multiplier <= 6):
        return 0.6
    elif(multiplier >= 7 and multiplier <= 9):
        return 0.4
    elif(multiplier >= 10):
        return 0.2

def score_differential_multiplier(play):
    """
    Applies a multiplier based on the difference between scores.
    When tied - 2x.
    When losing by 2+ scores - 3x.
    When losing by 1 score - 4x.
    When winning - 1x.
    Arg: diff: integer representing score differential.
    Returns: integer to be used as multiplier.
    """
    diff = score_differential(play)
    
    if(diff > 0):
        return 1
    elif(diff == 0):
        return 2
    elif(diff < -8):
        return 3
    else:
        return 4

def surrender_index(play):
    """
    Calculates the surrender index of the punt.
    Arg: play: Play object.
    Returns: float of surrender index score.
    """
    surr = yard_line_multiplier(play) * first_down_distance_multiplier(play) * score_differential_multiplier(play) * clock_multiplier(play)
    return surr

def surrender_index_all_punts(punt_list):
    """
    Calculates surrender index of all punts in the list.
    Arg: play_list: List of Play objects.
    Returns: List of float surrender indexes for all punts
    """
    new_list = []
    for i in punt_list:
        surr = surrender_index(i)
        new_list.append(surrender_index(i))
        
    return new_list

def score_at_play(play):
    """
    Gets the current score at the time of the play.
    (Does so by iterating up until the point of the play.)
    Arg: play: a Play object
    Returns: List containing score of home team, score of away team
    """
    # Identify home team and away team
    home_team = play.drive.game.home
    away_team = play.drive.game.away
    
    # Initialize score at beginning of game; score[0] = away, score[1] = home
    score = [0, 0]
    
    # Initialize current game's plays
    current_game = play.drive.game
    current_game_plays = nflgame.combine_plays([current_game])
    
    for i in current_game_plays:
        # Using this to truncate in case of play reviews
        description = i.desc
        
        # If this is the same play as our identified play
        if(play.desc == i.desc):
            return score
        
        # If the play was reviewed and reversed, truncate to actual result.
        if("and the play was REVERSED" in description):
            description = description.split("and the play was REVERSED.")[1]
        
        # Identify team in possession
        pos_team = i.data['posteam']
        
        # Identify if interception happens
        if("INTERCEPTED" in description):
            if(home_team == pos_team):
                pos_team = away_team # Possession changes hands
            else:
                pos_team = home_team
        
        # Identify if fumble recovery turnover happens
        if("RECOVERED by" in description):
            if("MUFFS" not in description): # Muffed punt recovered by kicking team, everything stays the same
                if(home_team == pos_team):
                    pos_team = away_team # Possession changes hands
                else:
                    pos_team = home_team
        
        # If a touchdown was scored
        if("TOUCHDOWN" in description):
            if(home_team == pos_team):
                score[1] += 6
            else:
                score[0] += 6
        
        # If a field goal is scored
        elif("field goal is GOOD" in description):
            if(home_team == pos_team):
                score[1] += 3
            else:
                score[0] += 3
        
        # If an extra point is scored
        elif("extra point is GOOD" in description):
            if(home_team == pos_team):
                score[1] += 1
            else:
                score[0] += 1
                
        # If two-point conversion is scored
        elif("TWO-POINT CONVERSION ATTEMPT" in description and "ATTEMPT SUCCEEDS" in description):
            if(home_team == pos_team):
                score[1] += 2
            else:
                score[0] += 2
                
        # If safety is scored
        elif("SAFETY" in description):
            if(home_team == pos_team):
                score[0] += 2 # Because on a safety, the other team gets points
            else:
                score[1] += 2
    
    # Ideally we never have to return from here because we find the play
    print("PLAY NOT FOUND")
    return score

def get_final_stackrank(punts):
    """
    Gets the final stackrank for all punts in the list (punts).
    Arg: punts: a List of Play objects.
    Returns: stackranked array of punts and their surrender indices.
    """
    # Find surrender index for each punt
    all_surrender_index = surrender_index_all_punts(punts)
    
    # Grab final numpy array sorted to find punts with the highest surrender index
    final = []

    for i in range(len(all_surrender_index)):
        final.append((punts[i], all_surrender_index[i]))

    final = np.array(final)

    final[:, 1]
    final = final[final[:, 1].argsort()]
    return final[::-1]

if __name__ == "__main__":
    years = range(2009, 2019)
    weeks = range(1, 18)
    seasons_dict = {}

    for i in years:
        week_dict = {}
        for j in weeks:
            try:
                week_dict[j] = nflgame.games(i, week=j)
            except:
                print("YEAR {} WEEK {} FAILED".format(i, j))
        
        seasons_dict[i] = week_dict

    punts = []
    for i in years:
        for j in weeks:
            try:
                for game in seasons_dict[i][j]:
                    for play in nflgame.combine_plays([game]):
                        if("punts" in play.desc):
                            punts.append(play)
            except:
                print("Exception Found in SEASON {} WEEK {}".format(i, j))
    
    print("RESULTS: ", get_final_stackrank(punts))