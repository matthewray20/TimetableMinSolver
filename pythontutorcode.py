class Day:
    def __init__(self, name, lessons):
        self.name = name
        self.lessons = lessons
    
    def print_line(self):
        minm, maxm = 8, 16
    
    
class Week:
    def __init__(self):
        self.days = [
            Day('Mon', [(9, 10), (11, 13)]),
            Day('Tue', [(8, 10), (10, 11), (15, 16)])]
            
        self.end_str = '| '
    
    def display(self):
        day_displayers = []
        for day in self.days:
            print("{name:^{length}}".format(length = 14, name=day.name), end = self.end_str)
            day_displayers.append(day.print_line())
        # print break line
        print('\n-------------------------------')
    
    
    
tt = Week()
tt.display()
    
    
    