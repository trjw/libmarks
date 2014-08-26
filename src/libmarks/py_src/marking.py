from __future__ import print_function

import os
import multiprocessing as mp
import csv
import json
from .runner import BasicTestRunner, MarkingTestRunner


NUM_PROCESSES = 4


def mark_submission(path, test, flags):
    """Mark a single submission"""
    try:
        # Change to submission directory.
        os.chdir(path)

        # Get submission ID (directory name).
        submission = os.path.basename(os.path.normpath(path))

        print("Starting marking submission:", submission)

        # Set marking mode to be silent.
        flags['silent'] = True

        # Enable cleanup.
        flags['cleanup'] = True

        # Run the tests.
        runner = MarkingTestRunner(**flags)
        result = runner.run(test)

        # Export the results and save them as JSON.
        details = result.export()
        details['submission'] = submission

        with open('results.json', 'w') as f:
            json.dump(details, f, indent=4)

        print("Finished marking submission:", submission)
        return details
    except KeyboardInterrupt:
        return


class MarkingRunner(BasicTestRunner):

    def _list_dirs(self):
        """List all directories within the target directory"""
        path = self.flags.get('directory')
        return filter(os.path.isdir, os.listdir(path))

    def _submissions(self, test):
        """Generator returning path, test and flags"""
        for path in self._list_dirs():
            full_path = os.path.join(self.flags['working_dir'], path)
            yield full_path, test, self.flags

    def run(self, test):
        # Get number of processes to run
        processes = self.flags.get('processes', NUM_PROCESSES)

        # Run tests over all submissions
        pool = mp.Pool(processes=processes)
        results = []

        def complete(result):
            # Record results from marking
            if result:
                results.append(result)

        try:
            for s in self._submissions(test):
                pool.apply_async(mark_submission, args=s, callback=complete)
            pool.close()
            pool.join()
        except KeyboardInterrupt:
            pool.terminate()
            pool.join()

        # Save output as JSON.
        with open('overall_results.json', 'w') as f:
            json.dump(results, f)

        if results:
            # Save test results to CSV.
            # Create header - include test names.
            header = ['submission']
            # TODO: Get list of test names, outside of tests
            header.extend(results[0]['tests'].keys())
            header.extend(results[0]['details'].keys())
            header.append('mark')

            with open('marking_results.csv', 'w') as f:
                dw = csv.DictWriter(f, fieldnames=header)
                dw.writerow(dict((fn, fn) for fn in header))
                for res in results:
                    info = {
                        'submission': res['submission'],
                        'mark': res['totals']['received_marks']
                    }
                    info.update(res['tests'])
                    info.update(res['details'])
                    dw.writerow(info)
