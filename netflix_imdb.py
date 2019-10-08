from selenium import webdriver
from selenium.webdriver.common.keys import Keys

import sys
import time
import re
import json
import datetime

from PySide2 import QtWidgets
from PySide2 import QtGui
from PySide2 import QtCore

# Every Qt application must have one and only one QApplication object;
# it receives the command line arguments passed to the script, as they
# can be used to customize the application's appearance and behavior
qt_app = QtWidgets.QApplication(sys.argv)


class NetflixBot(QtWidgets.QWidget):
    def __init__(self, email, password, username):
        self.email = email
        self.password = password
        self.username = username

        # Declare browser bot
        self.browser = webdriver.Firefox()

        # Declare dictionary and list to store netflix titles
        self.data_dict = dict()
        self.titles = []
        self.load_cache = True

        self.sorted_keys = []
        self.sorted_score_top = False
        self.sorted_type_top = False
        self.sorted_year_top = False
        self.sorted_duration_top = False

        # Declare json path for caching
        self.json_path = './data/list.json'

        # Login to netflix and fetch titles on your list
        self.login()
        # self.titles = ['Pixels', 'Tom and Jerry: The Movie', 'The Fresh Prince of Bel-Air', 'V for Vendetta', 'Rick and Morty', 'Naruto', 'MINDHUNTER', 'Django Unchained', 'How I Met Your Mother', 'Forrest Gump', 'The Discovery', 'Burning Sands', 'Ali G Indahouse', 'Brooklyn Nine-Nine', 'Stranger Things', 'Lucifer', 'World War II in Colour', 'Once Upon a Time', 'The Wandering Earth', 'Breaking Bad', 'Bill Burr: Paper Tiger', 'Explained', 'The Last Kingdom', 'Sherlock', 'Love, Death & Robots', 'Travis Scott: Look Mom I Can Fly', 'Death Note', 'Blade Runner 2049', 'Ted 2', 'The 100', 'Dark', 'The Matrix', 'Shadowhunters: The Mortal Instruments', 'The Wolf of Wall Street', 'Arthdal Chronicles']
        print('Found the following titles in your list: %s' % self.titles)

        if self.load_cache:
            # Read in data dict that is already saved
            self.json_path = './data/list.json'
            with open(self.json_path) as json_file:
                data = json.load(json_file)

            # Remove the keys that already have info from the list
            for key in data.keys():
                print('%s\'s data is cached' % key)

                try:
                    self.titles.remove(key)
                except ValueError:
                    continue

        if len(self.titles) > 0:
            # If there are new titles, look up their data
            self.check_ratings()

        if self.load_cache:
            # Combine new dict with the old dict
            self.data_dict = {**self.data_dict, **data}

        # Cache data dict
        with open(self.json_path, 'w') as json_file:
            json.dump(self.data_dict, json_file)

        # Close browser
        self.browser.close()

        # Sort titles by score
        self.sorted_keys = [title for title in sorted(
            self.data_dict.keys(),
            key=lambda x: self.data_dict[x]['score'],
            reverse=True
        )]

        # Do widget things
        QtWidgets.QWidget.__init__(self)

        # Define main layout of the application
        self.layout = QtWidgets.QVBoxLayout()

        # Label for user on the top
        self.user_label = QtWidgets.QLabel('Welcome, %s' % self.username)
        self.layout.addWidget(self.user_label)

        # Table view for all titles and their data in your list on Netflix
        self.table_view = QtWidgets.QTableWidget()
        self.table_view.setEditTriggers(
            QtWidgets.QAbstractItemView.NoEditTriggers
        )
        self.table_view.setFocusPolicy(QtGui.Qt.NoFocus)
        self.table_view.horizontalHeader().setStretchLastSection(True)

        # Connect horizontal header item click to self.sort_column function
        self.connect(
            self.table_view.horizontalHeader(),
            QtCore.SIGNAL('sectionClicked(int)'),
            self.sort_column
        )

        # Setup tableview
        self.setup_tableview()

        # Add widget to the layout
        self.layout.addWidget(self.table_view)

        # Finalizing widget
        self.setLayout(self.layout)
        # Ensure window opens visibly
        self.setWindowFlag(QtCore.Qt.WindowStaysOnTopHint)
        # Set title of the window
        self.setWindowTitle('Netflix List of %s' % self.username)

    def setup_tableview(self):
        """
        This function will set up the tableview widget that is used to display
        all the data for all the titles in your list.
        """

        # Reset the widget
        self.table_view.clear()

        self.table_view.setRowCount(len(self.sorted_keys))
        self.table_view.setColumnCount(8)

        # Set the horizontal headers' text and column width
        self.table_view.setHorizontalHeaderItem(0, QtWidgets.QTableWidgetItem('Title'))
        self.table_view.setColumnWidth(0, 150)

        self.table_view.setHorizontalHeaderItem(1, QtWidgets.QTableWidgetItem('Type'))
        self.table_view.setColumnWidth(1, 65)

        self.table_view.setHorizontalHeaderItem(2, QtWidgets.QTableWidgetItem('Score'))
        self.table_view.setColumnWidth(2, 60)

        self.table_view.setHorizontalHeaderItem(3, QtWidgets.QTableWidgetItem('Genre'))
        self.table_view.setColumnWidth(3, 150)

        self.table_view.setHorizontalHeaderItem(4, QtWidgets.QTableWidgetItem('Duration'))
        self.table_view.setColumnWidth(4, 300)

        self.table_view.setHorizontalHeaderItem(5, QtWidgets.QTableWidgetItem('Release Date'))
        self.table_view.setColumnWidth(5, 150)

        self.table_view.setHorizontalHeaderItem(6, QtWidgets.QTableWidgetItem('Credits'))
        self.table_view.setColumnWidth(6, 350)

        self.table_view.setHorizontalHeaderItem(7, QtWidgets.QTableWidgetItem('Summary'))
        self.table_view.setColumnWidth(7, 350)

        '''
        self.data_dict[title] = {
            'score': score,             → 7.7
            'summary': summary,         → 'Some string'
            'duration': duration,       → '100 episodes (7 Seasons in 2020), 43min per Episode' / '1h 55min'
            'credits': creds_list,      → ['Creators: some dude', 'Stars: hero, his chick, evil dude']
            'genres': genres,           → ['Drama', 'Fantasy', 'Comedy']
            'released': year,           → 2016
            'type': show_type,          → 'Movie' / 'Serie'
        }
        '''

        for i, title in enumerate(self.sorted_keys):

            # Adjust certain keys for better displaying
            title_genres = ', '.join(self.data_dict[title]['genres'])
            title_credits = '\n'.join(self.data_dict[title]['credits'])
            title_score = str(self.data_dict[title]['score']) + '/10'

            # Set row height for each row depending on the amount of credits
            # (Producers:, Writers:, Stars: // Producers:, Stars:)
            self.table_view.setRowHeight(i, len(self.data_dict[title]['credits']) * 25)

            # Add column data for each row
            self.table_view.setItem(i, 0, QtWidgets.QTableWidgetItem(title))
            self.table_view.setItem(i, 1, QtWidgets.QTableWidgetItem(self.data_dict[title]['type']))
            self.table_view.setItem(i, 2, QtWidgets.QTableWidgetItem(title_score))
            self.table_view.setItem(i, 3, QtWidgets.QTableWidgetItem(title_genres))
            self.table_view.setItem(i, 4, QtWidgets.QTableWidgetItem(self.data_dict[title]['duration']))
            self.table_view.setItem(i, 5, QtWidgets.QTableWidgetItem(self.data_dict[title]['released']))
            self.table_view.setItem(i, 6, QtWidgets.QTableWidgetItem(title_credits))
            self.table_view.setItem(i, 7, QtWidgets.QTableWidgetItem(self.data_dict[title]['summary']))

    def sort_column(self, column):
        """
        Sorts the column you have clicked on, after sorting the list of titles, this function will call the table widget setup function
        :param column: index of the column that was clicked
        """
        if column == 1:  # type
            self.sorted_keys = sorted(self.data_dict.keys(),
                                      key=lambda x: (self.data_dict[x]['type']),
                                      reverse=self.sorted_type_top)
            # Invert sorting method
            self.sorted_type_top = not self.sorted_type_top

        elif column == 2:    # Score
            self.sorted_keys = sorted(self.data_dict.keys(),
                                      key=lambda x: (float(self.data_dict[x]['score'])),
                                      reverse=self.sorted_score_top)
            # Invert sorting method
            self.sorted_score_top = not self.sorted_score_top

        elif column == 4:    # Duration
            d = dict()
            for k in self.sorted_keys:
                duration_string = self.data_dict[k]['duration']

                # Get amount of episodes
                if 'episode' in duration_string:
                    if 'Some' in duration_string:
                        episodes = 0
                    else:
                        episodes = int(duration_string.split(' episodes')[0])
                else:
                    episodes = 1

                # Get the duration in minutes
                minutes = 0
                if 'min' in duration_string:
                    minutes = int(re.findall('([0-9]+)min', duration_string)[0])
                if 'h' in duration_string:
                    minutes += int(re.findall('([0-9]+)h', duration_string)[0]) * 60

                # Get total duration of the whole show
                minutes *= episodes

                # Store it for sorting
                d[k] = minutes

            # Sort titles based on duration
            self.sorted_keys = sorted(d.keys(),
                                      key=lambda x: d[x],
                                      reverse=self.sorted_duration_top)
            # Invert sorting method
            self.sorted_duration_top = not self.sorted_duration_top

        elif column == 5:    # release year
            self.sorted_keys = sorted(self.data_dict.keys(),
                                      key=lambda x: (float(self.data_dict[x]['released'])),
                                      reverse=self.sorted_year_top)
            # Invert sorting method
            self.sorted_year_top = not self.sorted_year_top

        if column != 2:
            # Make sure next time we click to sort by score,
            # the highest score is on top
            self.sorted_score_top = True

        # Redraw the table
        self.setup_tableview()

    def login(self):
        """
        Logs you into netflix using specified email, password and username.
        If the login worked, it will call a function that retrieves the titles
        from your watch list. These are stored in the self.titles variable
        """
        # Browse to login url
        self.browser.get('https://www.netflix.com/be/login')

        time.sleep(3)

        # define email and password input fields
        email = self.browser.find_element_by_id('id_userLoginId')
        password = self.browser.find_element_by_id('id_password')

        # clear the input fields
        email.clear()
        password.clear()

        # put in the login info
        email.send_keys(self.email)
        password.send_keys(self.password)

        # submit
        password.send_keys(Keys.RETURN)

        time.sleep(3)

        # Check profiles for the given user
        profiles = self.browser.find_elements_by_class_name('profile')
        user_found = False

        for profile in profiles:
            profile_name = str(
                profile.find_element_by_class_name('profile-name').text
            )

            if profile_name == self.username:
                user_found = True
                profile.find_element_by_class_name('profile-icon').click()

                time.sleep(3)

                self.browser.get('https://www.netflix.com/browse/my-list')

                time.sleep(3)

                my_list_items = self.browser.find_elements_by_class_name('fallback-text')
                return_arr = []

                for item in my_list_items:
                    return_arr.append(str(item.text))

                # Fetch items on this user's list
                self.titles = list(set(return_arr))
                break

        if not user_found:
            print('%s is not a user of this account' % self.username)

    def check_ratings(self):
        """
        Check each title on your watch list and fetches the follwoing data
            - Duration
            - Score
            - Release Date
            - Amount of seasons
            - Credits (Creators, Writers, Directors, Stars)
            - Summary
            - Genres
            - Show type (Movie/Serie)
        :return: nested dictionary with titles as keys, and a dict of info about the title as values
        """

        self.browser.get('https://www.imdb.com/')

        for title in self.titles:
            input_bar = self.browser.find_element_by_id('navbar-query')
            input_bar.clear()

            input_bar.send_keys(title)
            input_bar.send_keys(Keys.RETURN)

            time.sleep(3)

            # Click on the first suggestion
            css_selector = "div.findSection:nth-child(3) > table:nth-child(2) > tbody:nth-child(1) > tr:nth-child(1) > td:nth-child(2) > a:nth-child(1)"
            self.browser.find_element_by_css_selector(css_selector).click()
            time.sleep(3)

            # Pull details that will always be available
            score = str(self.browser.find_element_by_class_name('ratingValue').text)
            score = score.split('/10')[0].replace(',', '.')

            time.sleep(3)

            summary = str(self.browser.find_element_by_class_name('summary_text').text)
            subtext = str(self.browser.find_element_by_class_name('subtext').text)

            # Pull details that differ between movies and series
            try:
                duration = str(self.browser.find_element_by_class_name('bp_sub_heading').text)  # Only for series
                if 'episodes' not in duration:
                    duration = 'Some episodes'
            except Exception:
                # bp_sub_heading won't be found on a movie page
                duration = 'movie'

            if subtext[0].isdigit():
                # Split up the details from the subtext
                subtext_list = subtext.split(' | ')
            else:
                # Some movies' subtext starts with 'R' / 'PG-13'
                subtext_list = subtext.split(' | ')
                del subtext_list[0]

            # Duration
            if duration == 'movie':
                show_type = 'Movie'
                duration = subtext_list[0]
                try:
                    year = datetime.datetime.strptime(subtext_list[2].split(' (')[0], '%d %B %Y').strftime('%Y')
                except ValueError:
                    year = str(subtext_list[2].split(' (')[0][-4:])

            else:   # series
                show_type = 'Serie'
                # Retrieve last season and its release date
                season_tab = str(self.browser.find_element_by_class_name('seasons-and-year-nav').text).strip()

                numbers = re.findall('[0-9]+', season_tab)
                latest_season = int(numbers[0])
                latest_year = int(max(numbers, key=lambda x: int(x)))

                duration += ' (%d Seasons in %d), %s per episode' % (latest_season, latest_year, subtext_list[0])

                year = re.findall('[0-9]+', subtext_list[2])[0]

            # Pull some more data out from the subtext
            genres = subtext_list[1].split(', ')

            # Pull details that are not always available
            creds_list = []
            creds = self.browser.find_elements_by_class_name('credit_summary_item')
            for c in creds:
                temp = str(c.text)
                if '|' in temp:
                    temp = temp.split('|')[0]

                creds_list.append(temp)

            self.data_dict[title] = {
                'score': score,
                'summary': summary,
                'duration': duration,
                'credits': creds_list,
                'genres': genres,
                'released': year,
                'type': show_type,
            }

    def run(self):
        # Show the window
        self.show()
        # Run the qt application
        qt_app.exec_()


# Replace these by your actual email, password and username
simon = NetflixBot('mysecretemail@gmail.com', 'mysecretpassword', 'Simon')
simon.run()
