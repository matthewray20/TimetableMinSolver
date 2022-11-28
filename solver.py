from datetime import datetime, timedelta
import json
from copy import deepcopy

# Constants
MIN_START = datetime.strptime('08:30', '%H:%M')
MAX_END = datetime.strptime('17:00', '%H:%M')
ALLOW_LECTURE_CLASH = True
MAX_TIME_WITHOUT_BREAK = 6

# TODO: constant min start max finish but implement a by day overruling
# TODO: build the constants into a json config file
# TODO: Delete multiple listings for same lesson time, have condition 
# to leave if they only have different weeks and we are using weeks in the assess()
# TODO: Fix ALLOW_LECTURE CLASH -> should not build lectures when False, currently does when True
# TODO: Merge and clean up can_add and addLesson

# Classes
class Day:
    def __init__(self, earliest=MIN_START, latest=MAX_END):
        self.earliest = earliest
        self.latest = latest
        self.lessons = []
    
    def display(self):
        pass

    def can_add(self, a_lesson_time):
        # check against MIN_START and MAX_END
        if a_lesson_time.start_time < self.earliest or a_lesson_time.end_time > self.latest:
            return False

        # now check if it fits into the classes of the day
        length = len(self.lessons)
        # check no lessons in the day
        if  length == 0:
            return True
        elif length == 1:
            # new lesson starts after current one finishes OR new lesson ends before current one starts
            if (self.lessons[0].end_time <= a_lesson_time.start_time) or (a_lesson_time.end_time <= self.lessons[0].start_time):
                return True
        else:
            # check added to the start or end
            if a_lesson_time.end_time >= self.lessons[-1].end_time or a_lesson_time.end_time <= self.lessons[0].start_time:
                return True
            # reverse so first one less than a_lesson_time.start_time is the one next to it
            for i in range(length-1, -1, -1):
                # new lesson starts after previous one ends AND finishes before next one starts 
                if (self.lessons[i].end_time <= a_lesson_time.start_time) and (a_lesson_time.end_time <= self.lessons[i-1].start_time):
                    return True

        return False

    def addLesson(self, a_lesson_time):
        # assuming can_add has been called so no lesson will be appended when doesnt fit
        self.lessons.append(a_lesson_time)
        # using bubble sort to organise lessons by start time
        # could insert lesson in its spot and make a new list, but sorting seems like more interesting code
        length = len(self.lessons)
        for i in range(length-1):
            for j in range(length-1-i):
                if self.lessons[j].start_time > self.lessons[j+1].start_time:
                    tmp = self.lessons[j]
                    self.lessons[j] = self.lessons[j+1]
                    self.lessons[j+1] = tmp
        return

    def removeLesson(self, a_lesson_time):
        # check and then remove a lesson time from the day
        if a_lesson_time in self.lessons:
            self.lessons.remove(a_lesson_time)
        return

    

class Week:
    def __init__(self):
        self.day_names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        self.days = [Day() for i in range(len(self.day_names))]

    def display(self, start_range=1, stop_range=7):
        # TODO: make a nice print out
        pass
    
    def can_add(self, a_lesson_time):
        return self.days[a_lesson_time.day_no].can_add(a_lesson_time)

    def add(self, a_lesson_time):
        self.days[a_lesson_time.day_no].addLesson(a_lesson_time)
        return

    def remove(self, a_lesson_time):
        self.days[a_lesson_time.day_no].removeLesson(a_lesson_time)
        return
    
    def assess(self):
        # CRITERIA: in order of importance 
        # min days in
        # min excess time per day
        # preference early finishes: calculated as timedelta from MAX_END (bigger is better)
        # no more than MAX_HOURS_WITHOUT_BREAK

        ### unsure if should return tuple of each value or generate a score based on them
        days_in = 0
        excess_time = timedelta(hours=0)
        average_finish = timedelta(hours=0)
        break_constraint = timedelta(hours=MAX_TIME_WITHOUT_BREAK)
        satisfies_break_constaint = True

        for day in self.days:
            # empty day continue to next
            if day.lessons == []:
                continue
            # this day has classes, update days_in
            days_in += 1
            # average finish time
            average_finish += day.latest - day.lessons[-1].end_time
            time_without_break_counter = timedelta(hours=0)
            # calculate excess time and judge 
            print('length:', len(day.lessons))
            for i in range(len(day.lessons)-1):
                excess_time += abs(day.lessons[i+1].start_time - day.lessons[i].end_time)
                if day.lessons[i].end_time == day.lessons[i+1].start_time:
                    # no break between lessons, add duration of current lesson
                    time_without_break_counter += day.lessons[i].end_time - day.lessons[i].start_time
                    # check this doesn't break the break time constaint
                    if time_without_break_counter > break_constraint:
                        satisfies_break_constaint = False
                    else:
                        time_without_break_counter = timedelta(hours=0)

        return (days_in, excess_time, average_finish/days_in, satisfies_break_constaint)



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
    


# Functions
def buildLessons(filename):
    all_lessons = []
    with open(filename) as f:
        data = json.load(f)
        # go into data through all the times easch lesson has
        for course in data["courses"]:
            for lesson in course["lessons"]:
                # don't build lectures if ALLOW_LECTURE_CLASH = TRUE
                if not (lesson["type"] == "LTL" and not ALLOW_LECTURE_CLASH):
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
                        if a_time["availability"] != "notfull":
                            # make the LessonTime class
                            a_lesson.times.append(LessonTime(
                                a_time["day_no"]-1, # to account for day numbers starting at 1
                                a_time["start_time"],
                                a_lesson # back link to master lesson to access Lesson info
                            ))
                            
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
    global lessons
    if n < len(lessons):
        for lesson_time in lessons[n].times:
            if timetable.can_add(lesson_time):
                # add, search, remove for next next level up's search
                timetable.add(lesson_time)
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
    global timetable
    global lessons
    timetable = Week()
    lessons = buildLessons('lessonOptionsReDone.json')
    
    # basic results that will definately be overwritten
    initial_results = (7, timedelta(hours=0), timedelta(hours=0), True)
    # recursive depth first search
    print('beginning search')
    best_timetable, best_results = depth_first_search(0, [], initial_results)
    print(f'we have {len(best_timetable)} best timetable(s)')
    print(best_results)
    # basic timetable print
    somelen = len(best_timetable[0].days)
    print(somelen)
    for i in range(somelen):
        print(timetable.day_names[i])
        for lesson_time in best_timetable[0].days[i].lessons:
            print(lesson_time.master_lesson.course_code, lesson_time.master_lesson.type)
            print(lesson_time.start_time, lesson_time.master_lesson.duration)
            print()
    


if __name__ == '__main__':
    # global variables
    global timetable
    global lessons
    main()