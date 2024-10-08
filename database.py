import yaml
import oracledb
# Import required library for making HTTP requests
import requests


with open('config.yaml', 'r') as file:
    config_data = yaml.safe_load(file)

db_username = config_data['db_username']
db_password = config_data['db_password']
db_dsn = config_data['db_dsn']

# Initialize the Oracle Client library
oracledb.init_oracle_client()

class OracleDBInterface:
    def __init__(self, username, password, dsn):
        self.username = username
        self.password = password
        self.dsn = dsn
        self.connection = None

    def connect(self):
        try:
            self.connection = oracledb.connect(
                user=self.username,
                password=self.password,
                dsn=self.dsn,            )
            print("Successfully connected to foosball db")
        except oracledb.Error as error:
            print(f"Error connecting to foosball db: {error}")

    def disconnect(self):
        if self.connection:
            self.connection.close()
            print("Disconnected from foosball db")

    def execute_query(self, query):
        if not self.connection:
            print("Not connected to the db. Call connect() first.")
            return None

        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query)
                columns = [col[0] for col in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except oracledb.Error as error:
            print(f"Error executing query: {error}")
            return None

    def get_goals_per_team(self):
        query = """
        SELECT
            TRIM(GAMEDATATIMESTAMP) AS "GAMEDATATIMESTAMP",
            PLAYERDISPLAYNAME,
            count(PLAYER) "Total Goals Per Team"
        FROM EXDEMO.PROGRESSIVE_GAME_GOALS_VIEW
        where GAMEEVENTTYPEID = 63
        and TRIM(GAMEDATATIMESTAMP) = (select max(trim(GAMEDATATIMESTAMP)) from  EXDEMO.CURRENT_GAME_VEGAS_GOALS_V)
        group by PLAYERDISPLAYNAME, TRIM(GAMEDATATIMESTAMP)
        order by PLAYERDISPLAYNAME;
        """
        return self.execute_query(query)

    def get_possession_percentage(self):
        query = """
        SELECT
            TRIM(GAMEDATATIMESTAMP) AS "GAMEDATATIMESTAMP",
            ROUND(AVG(PLAYER1_POSSESSION_PCT),2) AS PLAYER1_POSSESSION_PCT,
            ROUND(AVG(PLAYER2_POSSESSION_PCT),2) AS PLAYER2_POSSESSION_PCT
        FROM
            EXDEMO.OAC_PROGRESSIVE_GAME_STATS
        GROUP BY TRIM(GAMEDATATIMESTAMP)
        ORDER BY TRIM(GAMEDATATIMESTAMP);
        """
        return self.execute_query(query)

    def get_possession_total(self):
        query = """
        SELECT
            TRIM(GAMEDATATIMESTAMP) AS "GAMEDATATIMESTAMP",
            sum(PLAYER1_MATCH_DURATION_SECONDS) "Total Cummulate Possession by Player1 (in seconds)",
            ROUND(AVG(PLAYER1_MATCH_DURATION_SECONDS),2) "Average Possession by Player1 (in seconds)", 
            sum(PLAYER2_MATCH_DURATION_SECONDS) "Total Cummulate Possession by Player2 (in seconds)",
            ROUND(AVG(PLAYER2_MATCH_DURATION_SECONDS),2) "Average Possession by Player2 (in seconds)"
        FROM
            EXDEMO.OAC_PROGRESSIVE_GAME_STATS
        GROUP BY TRIM(GAMEDATATIMESTAMP)
        ORDER BY TRIM(GAMEDATATIMESTAMP);
        """
        return self.execute_query(query)

    def get_match_duration(self):
        query = """
        SELECT
            TRIM(GAMEDATATIMESTAMP) AS "GAMEDATATIMESTAMP",
            sum(match_duration_seconds) "Total Cummulative Match Time (in seconds)"
        FROM
            EXDEMO.OAC_PROGRESSIVE_GAME_STATS
        GROUP BY TRIM(GAMEDATATIMESTAMP)
        ORDER BY TRIM(GAMEDATATIMESTAMP);
        """
        return self.execute_query(query)

    def get_number_of_players_and_games_played(self):
        query = """
        SELECT
            TRIM(GAMEDATATIMESTAMP) AS "GAMEDATATIMESTAMP",
            sum(num_of_players) "Total Number of Players",
            sum(num_of_players)/2 "Total Number of Games" 
        FROM
            EXDEMO.OAC_PROGRESSIVE_GAME_STATS
        GROUP BY TRIM(GAMEDATATIMESTAMP)
        ORDER BY TRIM(GAMEDATATIMESTAMP);
        """
        return self.execute_query(query)




def main():
    
    db = OracleDBInterface(db_username, db_password, db_dsn)
    db.connect()

    # Example: Get goals per team
    goals_per_team = db.get_goals_per_team()
    print("Goals per team:", goals_per_team)
    # Get possession percentage
    possession_percentage = db.get_possession_percentage()
    print("Possession percentage:", possession_percentage)

    # Get possession total
    possession_total = db.get_possession_total()
    print("Possession total:", possession_total)

    # Get match duration
    match_duration = db.get_match_duration()
    print("Match duration:", match_duration)

    # Get number of players and games played
    number_of_players_and_games_played = db.get_number_of_players_and_games_played()

    #print(goals_per_team, possession_percentage, possession_total, match_duration, number_of_players_and_games_played)


    # Prepare the data to be sent
    data = {
        "goals_per_team": str(goals_per_team),
        "possession_percentage": str(possession_percentage),
        "possession_total": str(possession_total),
        "match_duration": str(match_duration),
        "number_of_players_and_games_played": str(number_of_players_and_games_played)
    }

    #print(data)

    # Send GET request to localhost:3500
    try:
        response = requests.get('http://localhost:3500/generate', params=data)
        response.raise_for_status()  # Raise an exception for bad status codes
        print("Data sent successfully. Response:", response.text)
    except (requests.RequestException, Exception) as e:
        print("Error sending data to OCI GenAI service:", e)

    db.disconnect()


# Example usage
if __name__ == "__main__":
    main()
