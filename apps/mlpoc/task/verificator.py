import logging
import os

from apps.core.task.verificator import CoreVerificator, SubtaskVerificationState
from apps.mlpoc.mlpocenvironment import MLPOCTaskEnvironment
from golem.resource.dirmanager import find_task_script
from golem.task.localcomputer import LocalComputer
from golem.task.taskbase import ComputeTaskDef

logger = logging.getLogger("apps.mlpoc")


class MLPOCTaskVerificator(CoreVerificator):
    SCRIPT_NAME = "requestor_verificator.py"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.verification_options = {}
        self.verification_error = False

    def __verification_success(self, results, time_spent):
        logger.info("Advance verification finished")
        self.verification_error = False

    def __verification_failure(self, error):
        logger.info("Advance verification failure {}".format(error))
        self.verification_error = True

    def _load_src(self):
        script_name = find_task_script(MLPOCTaskEnvironment.APP_DIR,
                                       self.SCRIPT_NAME)
        with open(script_name, "r") as f:
            src = f.read()
        return src

    def __query_extra_data(self, steps):
        ctd = ComputeTaskDef()
        ctd.extra_data["STEPS_PER_EPOCH"] = steps
        ctd.src_code = self._load_src()
        return ctd

    def _check_files(self, subtask_id, subtask_info, tr_files, task):
        query_extra_data = lambda: self.__query_extra_data(subtask_info["STEPS_PER_EPOCH"])
        computer = LocalComputer(None,  # we don't use task at all
                                 "",
                                 self.__verification_success,
                                 self.__verification_failure,
                                 query_extra_data,
                                 additional_resources=tr_files,
                                 use_task_resources=False)
        computer.run()
        if computer.tt is not None:
            computer.tt.join()
        else:
            self.ver_states[subtask_id] = SubtaskVerificationState.WRONG_ANSWER
        if self.verification_error:
            self.ver_states[subtask_id] = SubtaskVerificationState.WRONG_ANSWER
        # TODO only for debugging
        stderr = [x for x in computer.tt.result['data']
                  if os.path.basename(x) == "stderr.log"]

        self.ver_states[subtask_id] = SubtaskVerificationState.VERIFIED
