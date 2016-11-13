from __future__ import division, print_function

import os
import traceback
import copy
import multiprocessing as mp
from multiprocessing.pool import Pool
import csv
import json
import datetime
from .runner import BasicTestRunner, MarkingTestRunner


NUM_PROCESSES = 4
RESULTS_FILENAME = 'results.json'


class LogException(object):
    """Log any exception raised in a Pool worker"""

    def __init__(self, callable):
        self.__callable = callable

    def __call__(self, *args, **kwargs):
        try:
            result = self.__callable(*args, **kwargs)
        except Exception:
            self._error(traceback.format_exc())
            raise
        return result

    def _error(self, msg, *args):
        return mp.get_logger().error(msg, *args)


class LoggingPool(Pool):

    def apply_async(self, func, args=(), kwds={}, callback=None):
        return Pool.apply_async(self, LogException(func), args, kwds, callback)


def mark_submission(path, test, options):
    """Mark a single submission"""
    try:
        # Change to submission directory.
        os.chdir(path)

        # Get submission ID (directory name).
        submission = os.path.basename(os.path.normpath(path))
        options['submission'] = submission

        print("-> Start marking submission:", submission)

        details = None
        if options.get('resume', False) and os.path.exists(RESULTS_FILENAME):
            # Attempt to load results
            try:
                with open('results.json', 'r') as f:
                    details = json.load(f)
            except ValueError:
                # We will run the tests again for this one
                pass

        if details is None:
            # Set marking mode to be silent.
            options['silent'] = True

            # Enable cleanup.
            options['cleanup'] = True

            # Allow custom setup to be performed via function callback
            if options.get('marking_setup', False):
                options['marking_setup'](options)

            # Run the tests.
            runner = MarkingTestRunner(**options)
            result = runner.run(test)

            # Allow custom teardown to be performed via function callback
            if options.get('marking_tear_down', False):
                options['marking_tear_down'](options)

            # Export the results and save them as JSON.
            details = result.export()
            details['submission'] = submission

            with open(RESULTS_FILENAME, 'w') as f:
                json.dump(details, f, indent=4)

        print("-> Finished marking submission: {0} ({1})".format(
            submission, details['totals']['received_marks']))
        return details
    except KeyboardInterrupt:
        return


def load_submission_results(path, test, options):
    """Mark a single submission"""
    try:
        # Change to submission directory.
        os.chdir(path)

        # Get submission ID (directory name).
        submission = os.path.basename(os.path.normpath(path))
        options['submission'] = submission

        print("-> Start marking submission:", submission)

        details = None
        if os.path.exists(RESULTS_FILENAME):
            # Attempt to load results
            try:
                with open('results.json', 'r') as f:
                    details = json.load(f)
                print("-> Loaded results for submission: {0} ({1})".format(
                    submission, details['totals']['received_marks']))
            except ValueError:
                # We will run the tests again for this one
                pass

        if details is None:
            # Generate empty results
            details = {
                'submission': submission
            }

            print("-> Could not load results for submission: {0}".format(
                submission))

        return details
    except KeyboardInterrupt:
        return


class MarkingRunner(BasicTestRunner):

    def _list_dirs(self):
        """List all directories within the target directory"""
        dirs = []
        root = self.options.get('directory')
        for f in os.listdir(root):
            if os.path.isdir(os.path.join(root, f)):
                dirs.append(f)
        return dirs

    def _submissions(self, test):
        """Generator returning path, test and options"""
        for folder in self._list_dirs():
            full_path = os.path.join(self.options['directory'], folder)
            yield full_path, test, copy.deepcopy(self.options)

    def _set_protection(self):
        import marks
        preload = self.options.get('ld_preload', _default_protection())
        marks.set_ld_preload(preload)

    def _get_test_names(self, results):
        for res in results:
            tests = res.get('tests', None)
            if tests is not None:
                return sorted(tests.keys())
        return []

    def _get_detail_keys(self, results):
        detail_keys = set()
        for res in results:
            det = res.get('details', {})
            for k in det.keys():
                detail_keys.add(k)
        return sorted(detail_keys)

    def run(self, test):
        start_time = datetime.datetime.now()

        # Protect against potentially bad system calls
        self._set_protection()

        # Get number of processes to run
        processes = self.options.get('processes', NUM_PROCESSES)

        count = {
            'submissions': len(self._list_dirs()),
            'marked': 0,
        }
        print("Starting marking:", count['submissions'], "submissions")

        # Run tests over all submissions
        mp.log_to_stderr()
        pool = LoggingPool(processes=processes, maxtasksperchild=1)
        results = []

        def complete(result):
            # Record results from marking
            count['marked'] += 1
            print("Marked {0}/{1} ({2:.2%})".format(
                count['marked'],
                count['submissions'],
                count['marked'] / count['submissions']))
            if result:
                results.append(result)

        # Select which marking function to use
        marking_processor = mark_submission
        if self.options.get('tally', False):
            marking_processor = load_submission_results

        try:
            for s in self._submissions(test):
                pool.apply_async(marking_processor, args=s, callback=complete)
            pool.close()
            pool.join()
        except KeyboardInterrupt:
            pool.terminate()
            pool.join()

        # Create paths to output files
        directory = self.options.get('directory')

        run_time = start_time.strftime('%Y%m%d_%H%M%S')

        # Results JSON file
        results_json_filename = "overall_results_{0}.json".format(run_time)
        results_json_default = os.path.join(directory, results_json_filename)
        results_json = self.options.get(
            'overall_results_json', results_json_default)

        # Results CSV file
        results_csv_default = "marking_results_{0}.csv".format(run_time)
        results_csv_default = os.path.join(directory, results_csv_default)
        results_csv = self.options.get(
            'overall_results_csv', results_csv_default)

        # No results file
        no_results_filename = "no_results_{0}.txt".format(run_time)
        no_results_filename = os.path.join(directory, no_results_filename)
        no_results_path = self.options.get(
            'no_results_filename', no_results_filename)

        # Save output as JSON.
        with open(results_json, 'w') as f:
            json.dump(results, f)

        if results:
            no_result = []

            # Save test results to CSV.
            # Create header - include test names.
            header = ['submission']
            # TODO: Get list of test names, outside of tests
            header.extend(self._get_test_names(results))
            header.extend(self._get_detail_keys(results))
            header.append('mark')

            with open(results_csv, 'w') as f:
                dw = csv.DictWriter(f, fieldnames=header)
                dw.writerow(dict((fn, fn) for fn in header))
                for res in sorted(results, key=lambda x: x['submission']):
                    if 'tests' not in res:
                        no_result.append(res)
                        continue

                    info = {
                        'submission': res['submission'],
                        'mark': res['totals']['received_marks']
                    }
                    info.update(res['tests'])
                    info.update(res['details'])
                    dw.writerow(info)

            if no_result:
                with open(no_results_path, 'w') as f:
                    for res in no_result:
                        print(res['submission'], file=f)

        end_time = datetime.datetime.now()
        print("Time taken: ", str(end_time - start_time))


def _default_protection():
    """Get the path to the included protection library"""
    import marks
    return os.path.join(
        os.path.dirname(os.path.abspath(marks.__file__)), 'libprotect.so')
