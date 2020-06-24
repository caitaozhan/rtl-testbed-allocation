'''
Analyze the file_receive and see whether there is interference
'''

from collections import Counter

class TestInterfere:

    def __init__(self, rx_file):
        self.rx_file = rx_file

    def analyzefile(self):
        result = Counter()
        with open(self.rx_file, 'r') as f:
            for line in f:
                line = line.split()
                if len(line) == 4:
                    result[' '.join(line[2:])] += 1
                else:
                    result[' '.join(line)] += 1

        success = 0
        success_counter = 0
        fail    = 0

        for key, count in sorted(result.items(), key=lambda x: x[1], reverse=True):
            if count > 50:
                print(key, count)
                success += count
                success_counter += 1
            else:
                fail += count

        result = {'success_total':0, 'success_counter':0, 'success_average':0, 'fail_total':0, 'success_rate':0}
        try:
            # print('\nsuccess total   = {}'.format(success))
            # print('success count   = {}'.format(success_counter))
            # print('success average = {:d}'.format(success/success_counter))
            # print('fail total      = {}'.format(fail))
            # print('success rate    = {:.2f}%'.format(success*1.0/(success+fail)*100))
            result['success_total'] = success
            result['success_counter'] = success_counter
            result['success_average'] = success/success_counter
            result['fail_total'] = fail
            result['success_rate'] = success*1.0/(success+fail)*100
        except Exception as e:
            print(e)

        return result

    def test_interfere(self, success_count_threshold, success_rate_threshold, success_average_threshold):
        '''If there is interfere, then return True. If no interfere, then return False
        '''
        
        # print('success count   threshold', success_count_threshold)
        # print('success rate    threshold', success_rate_threshold)
        # print('success average threshold', success_average_threshold)
        result = self.analyzefile()
        for key, val in result.items():
            print(key, val)
        a = result['success_counter'] > success_count_threshold - 2
        b = result['success_rate'] > success_rate_threshold
        c = result['success_average'] > success_average_threshold
        if a and b and c:
            return False
        else:
            return True


def test():
    testinter = TestInterfere('file_receive')
    testinter.test_interfere(10, 99, 1000)


if __name__ == '__main__':
    test()
