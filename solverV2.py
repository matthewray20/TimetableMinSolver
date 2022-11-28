from datetime import datetime, timedelta
import json
from copy import deepcopy

class Lesson:
    def __init__(self, course_name, course_code, lesson_type, duration, location):
        self.course_name = course_name
        self.course_code = course_code
        self.type = lesson_type
        self.duration = duration
        self.location = location
        self.times = []



class LessonTime:
    def __init__(self, day_no, start_time, master_lesson):
        self.day_no = day_no
        self.start_time = datetime.strptime(start_time, '%H:%M')
        self.master_lesson = master_lesson
        self.end_time = self.start_time + timedelta(hours=self.master_lesson.duration)



class Day:
    def __init__(self, name, earliest, latest, master_week):
        self.name = name
        self.earliest = earliest
        self.latest = latest
        self.master_week = master_week
        self.lessons = []
    
    def display(self):
        num_times = int((self.master_week.weeks_latest-self.master_week.weeks_earliest).total_seconds()/1800)
        print_times = [self.master_week.weeks_earliest + i * timedelta(hours=0.5) for i in range(num_times+2)]
        empty_line = "{char:{fill_length}}".format(fill_length=self.master_week.cell_width, char='')
        lesson_divider = "{first_char:{fill}<{fill_length}}".format(first_char='', fill='-', fill_length=self.master_week.cell_width)
        
        within_lesson = False
        for i in range(len(print_times)-1):
            found_lesson = False
            prev_within_lesson = within_lesson
            within_lesson = False

            #lesson_at_prev_timestep = False
            for j in range(len(self.lessons)):
                if self.lessons[j].start_time == print_times[i]:
                    # set variables for yielding lesson
                    a_gen = self.lesson_print_generator(j)
                    found_lesson = True
                elif print_times[i] > self.lessons[j].start_time and print_times[i+1] <= self.lessons[j].end_time:
                    within_lesson = True

            if found_lesson or within_lesson:
                for _ in range(2):
                    yield next(a_gen)
            else:
                space_between_classes = [empty_line, empty_line]
                if prev_within_lesson: space_between_classes[0] = lesson_divider
                for line_to_print in space_between_classes:
                    yield line_to_print
        return

    def lesson_print_generator(self, n):
        lesson_divider = "{first_char:{fill}<{fill_length}}".format(first_char='', fill='-', fill_length=self.master_week.cell_width)
        empty_line = "{char:{fill_length}}".format(fill_length=self.master_week.cell_width, char='')
        
        yield lesson_divider
        yield "{code_and_type:{length}}".format(length=self.master_week.cell_width, code_and_type=self.lessons[n].master_lesson.course_code + ' ' + self.lessons[n].master_lesson.type)
        yield "{loc:{length}}".format(length=self.master_week.cell_width, loc=self.lessons[n].master_lesson.location)
        time_str = f'{self.lessons[n].start_time.hour}:{self.lessons[n].start_time.minute} - {self.lessons[n].end_time.hour}:{self.lessons[n].end_time.minute}'
        yield "{times:{length}}".format(length=self.master_week.cell_width, times=time_str)
        for _ in range(int(self.lessons[n].master_lesson.duration * 4 - 4)):
            yield empty_line
        yield lesson_divider

    def addLesson(self, a_lesson_time):
        # check if lesson breaks earliest or latest constraints
        if a_lesson_time.start_time < self.earliest or a_lesson_time.end_time > self.latest:
            return False
        length = len(self.lessons)
        # if no lesson times, add this lesson time
        if length == 0:
            self.lessons.append(a_lesson_time)
        else:
            # adding to start, end, somewhere middle of lesson list
            if a_lesson_time.end_time <= self.lessons[0].start_time:
                self.lessons.insert(0, a_lesson_time)
            elif a_lesson_time.start_time >= self.lessons[-1].end_time:
                self.lessons.insert(length, a_lesson_time)
            else:
                for i in range(length-1):
                    if self.lessons[i].end_time <= a_lesson_time.start_time and a_lesson_time.end_time <= self.lessons[i+1].start_time:
                        self.lessons.insert(i+1, a_lesson_time)
                        return True
                return False
        return True
        
    def removeLesson(self, a_lesson_time):
        # check and then remove a lesson time from the day
        if a_lesson_time in self.lessons:
            self.lessons.remove(a_lesson_time)
        return



class Week:
    def __init__(self, config):
        self.ALLOW_LECTURE_CLASH = config["consts"]["allow_lecture_clash"]
        self.MAX_TIME_WITHOUT_BREAK = config["consts"]["max_without_break"] 
        self.general_min_start = config["consts"]["general_min_start"]
        self.general_max_end = config["consts"]["general_max_end"]
        self.print_time_inc = config["consts"]["print_time_increment"]
        self.end_str = config["consts"]["print_division_string"]
        self.cell_width = config["consts"]["cell_width"]
        self.time_width = config["consts"]["time_width"]
        self.weeks_earliest = datetime.strptime(config["consts"]["general_min_start"], "%H:%M")
        self.weeks_latest = datetime.strptime(config["consts"]["general_max_end"], "%H:%M")
        self.days = []

        for a_day in config["days"]:
            if a_day["min_start"] == None or self.general_min_start == None: start = "01:00" # time that should be earlier than any possible class
            elif a_day["min_start"] == "": start = self.general_min_start # put in general start when undefined
            else: start = a_day["min_start"] # if specified, use that value

            if a_day["max_end"] == None or self.general_max_end == None: end = "23:00" # time that should be later than any possible class
            elif a_day["max_end"] == "": end = self.general_max_end # put in general start when undefined
            else: end = a_day["max_end"] # if specified, use that value

            self.days.append(Day(
                        a_day["name"], 
                        datetime.strptime(start, "%H:%M"), 
                        datetime.strptime(end, "%H:%M"),
                        self))

    def display(self):
        # day cell width is 14 characters
        line_break_str = "{first:{fill}<{fill_length}}".format(first='\n', fill='-', fill_length=self.time_width + len(self.end_str) + 7 * (self.cell_width + len(self.end_str)))
        empty_time_str = "{char:{length}}".format(length = self.time_width, char = '')
        # update weeks earliest and latest classes for printing range
        self.find_weeks_earliest_latest()
        # making print times list
        num_times = int(((self.weeks_latest-self.weeks_earliest).total_seconds()/(1800))) # get hours and double for num of half hour increments
        print_times = [self.weeks_earliest + i * timedelta(hours=0.5) for i in range(num_times+1)] # generate every time to print at

        # print top row with day names
        # print top left empty cell
        print(empty_time_str, end = self.end_str)
        # save displayers to a list and print day names
        day_displayers = []
        for day in self.days:
            print("{name:^{length}}".format(length = self.cell_width, name=day.name), end = self.end_str)
            day_displayers.append(day.display())
        # print break line
        print(line_break_str)
        
        # print the main body of the timetable
        # print lessons by day by line
        print_repeats = 0
        for time in print_times:
            for _ in range(2):
                # print time marking
                if print_repeats % int(self.print_time_inc * 4) == 0:
                    print("{tme:{length}}".format(length = self.time_width, tme = f'{time.hour}:{time.minute}'), end = self.end_str) # if i otherwise print left top emmpty cell one
                else:
                    print(empty_time_str, end=self.end_str)
                print_repeats += 1
                # printing lesson information
                for display_generator in day_displayers:
                    #next(display_generator)
                    print(next(display_generator), end = self.end_str)
                print('')
        print(line_break_str)

    def add(self, a_lesson_time):
        return self.days[a_lesson_time.day_no].addLesson(a_lesson_time)

    def remove(self, a_lesson_time):
        self.days[a_lesson_time.day_no].removeLesson(a_lesson_time)
        return

    def find_weeks_earliest_latest(self):
        # find the earliest and latest class times for the week
        # if none are earlier or later than the general constraints, return the general constraints
        # used for printing in display()
        for day in self.days:
            length = len(day.lessons)
            if length != 0:
                if day.lessons[0].start_time < self.weeks_earliest:
                    self.weeks_earliest = day.lessons[0].start_time
                if day.lessons[-1].end_time > self.weeks_latest:
                    self.weeks_latest = day.lessons[-1].end_time
        return 

    def assess(self):
        # CRITERIA: in order of importance 
        # min days in
        # min excess time per day
        # preference early finishes: calculated as timedelta from MAX_END (bigger is better)
        # no more than MAX_HOURS_WITHOUT_BREAK

        days_in = 0
        excess_time = average_finish = time_zero = timedelta(hours=0) # 2 time counters and a zero hours constant
        average_finish = timedelta(hours=0) # adding how many hrs early time finishes comp to day.latest -> if no limit on day.latest then don't count that day
        break_constraint = timedelta(hours=self.MAX_TIME_WITHOUT_BREAK)
        satisfies_break_constaint = True

        for day in self.days:
            # if the day is empty
            if len(day.lessons) == 0:
                continue
            # the day has classes, so update days_in
            days_in += 1
            # average early finish time
            average_finish += day.latest - day.lessons[-1].end_time
            # counter length of consecutive lessons
            time_without_break_counter = time_zero
            # iterating thrugh lessons
            length = len(day.lessons)
            for i in range(length-1):
                # add time spent in between classes
                time_diff = day.lessons[i+1].start_time - day.lessons[i].end_time
                if time_diff == time_zero:
                    # lessons go straight into each other
                    time_without_break_counter += timedelta(hours=day.lessons[i].master_lesson.duration)
                    # check if this breaks the constraint
                    if time_without_break_counter > break_constraint:
                        satisfies_break_constaint = False
                else:
                    # time_diff should only ever be positive here
                    excess_time += time_diff
                    # break between classes so reset counter
                    time_without_break_counter = time_zero

        return (days_in, excess_time, average_finish/days_in, satisfies_break_constaint)



# Functions
def buildLessons(filename, ALLOW_LECTURE_CLASH):
    all_lessons = []
    with open(filename) as f:
        data = json.load(f)
        # go into data through all the times easch lesson has
        for course in data["courses"]:
            for lesson in course["lessons"]:
                # don't build lectures if ALLOW_LECTURE_CLASH = TRUE
                if not lesson["type"] == "LTL" or ALLOW_LECTURE_CLASH:
                    # make Lesson class
                    a_lesson = Lesson(
                        course["name"],
                        course["code"],
                        lesson["type"],
                        lesson["duration"],
                        lesson["location"],
                    )

                    for a_time in lesson["times"]:
                        # don't build full classes
                        if a_time["availability"] != "notful":
                            # make the LessonTime class
                            a_lesson.times.append(LessonTime(
                                a_time["day_no"]-1, # to account for day numbers starting at 1
                                a_time["start_time"],
                                a_lesson)) # back link to master lesson to access Lesson info
                            
                    # save Lesson class with all its LessonTime classes
                    all_lessons.append(a_lesson)
    return all_lessons



def get_diff(data1, data2):
    data_diff = []
    for i in range(3):
        if data1[i] > data2[i] :
            data_diff.append(0)
        elif data1[i] == data2[i]:
            data_diff.append(1)
        else:
            data_diff.append(2)
    return data_diff



def depth_first_search(n, best_tt, best_res):
    global timetable
    global all_lessons
    if n < len(all_lessons):
        for lesson_time in all_lessons[n].times:
            # add, search, remove for next next level up's search
            result = timetable.add(lesson_time)
            if result:
                best_tt, best_res = depth_first_search(n+1, best_tt, best_res)
                timetable.remove(lesson_time)
    else:
        results = timetable.assess()
        if results[3]:
            res_diff = get_diff(best_res[:3], results[:3])
            if (res_diff[0]==0) or (res_diff[0]==1 and res_diff[1]==0) or (res_diff[0]==1 and res_diff[1]==1 and res_diff[2]==2):
                # new results are better
                best_tt = [deepcopy(timetable)]
                best_res = results
            elif res_diff[0] == 1 and res_diff[1] == 1 and res_diff[2] == 1:
                # results are the same
                best_tt.append(deepcopy(timetable))
    return best_tt, best_res
            


def main():
    # get constants from config file
    global timetable
    global all_lessons
    with open('config.json') as f:
        config = json.load(f)
    # build lesson data and week class instance
    print('Building all possible lesson times from the data...')
    print('Searching all possible lesson configurations...')
    all_lessons = buildLessons('sem2lessonOptions.json', config["consts"]["allow_lecture_clash"])
    timetable = Week(config)
    # searching for the best timetable
    initial_results = (7, timedelta(hours=23), timedelta(hours=0), True) # basic results that will definately be overwritten
    best_timetable, best_results = depth_first_search(0, [], initial_results)
    # asking user and then printing timetable
    print('Searching complete.\n\n')
    length = len(best_timetable)
    print(f'Found {length} best timetable(s) that give these results')
    if length != 0:
        print('number of days in:', best_results[0])
        print('excess time spent between classes:', best_results[1])
        print('average difference of finish time vs max end time:', best_results[2].total_seconds()/3600)
        print('Here is the first:')
        best_timetable[0].display()
    
    

if __name__ == '__main__':
    main()