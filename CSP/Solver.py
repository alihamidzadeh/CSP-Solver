import time
from typing import Optional

from CSP.Problem import Problem
from CSP.Variable import Variable


class Solver:

    def __init__(self, problem: Problem, use_mrv=False, use_lcv=False, use_forward_check=False):
        self.problem = problem
        self.use_lcv = use_lcv
        self.use_mrv = use_mrv
        self.use_forward_check = use_forward_check

    def is_finished(self) -> bool:
        return all([x.is_satisfied() for x in self.problem.constraints]) and len(
            self.problem.get_unassigned_variables()) == 0

    def solve(self):
        self.problem.calculate_neighbors()
        start = time.time()
        for var in self.problem.variables:
            if not self.forward_check(var):
                print("Problem Unsolvable")
                return
        result = self.backtracking()
        end = time.time()
        time_elapsed = (end - start) * 1000
        if result:
            print(f'Solved after {time_elapsed} ms')
        else:
            print(f'Failed to solve after {time_elapsed} ms')

    def backtracking(self):
        length_of_unassigned_variables = len(self.problem.get_unassigned_variables())
        if (length_of_unassigned_variables == 0):
            return True

        domain_snapshots = self.create_domain_snapshot()

        var = self.select_unassigned_variable()
        self.problem.print_assignments(var)
        for value in self.order_domain_values(var):
            domain_snapshots = self.create_domain_snapshot()
            var.value = value
            self.problem.print_assignments(var)
            if (self.is_consistent(var)):
                if ((not self.use_forward_check) or (self.forward_check(var))):
                    result = self.backtracking()
                    if (result == True):
                        return True

            var.value = None

        for v, domain_snapshot in domain_snapshots.items():
            v.domain = domain_snapshot
        return False

    def forward_check(self, var):
        nei = var.neighbors
        for neighbor in nei:
            if (not neighbor.has_value):
                nei_domain = neighbor.domain
                for other_var_candidate in nei_domain:
                    neighbor.value = other_var_candidate
                    if (not self.is_consistent(neighbor)):
                        neighbor.domain.remove(other_var_candidate)
                        if (len(neighbor.domain) == 0):
                            return False
                    neighbor.value = None
        return True

    def select_unassigned_variable(self) -> Optional[Variable]:
        if self.use_mrv:
            return self.mrv()
        unassigned_variables = self.problem.get_unassigned_variables()
        return unassigned_variables[0] if unassigned_variables else None

    def order_domain_values(self, var: Variable):
        if self.use_lcv:
            return self.lcv(var)
        return var.domain

    def mrv(self) -> Optional[Variable]:
        unassigned_variables = self.problem.get_unassigned_variables()
        if (not unassigned_variables):
            return None
        minimum_var = min(unassigned_variables, key=lambda var: len(var.domain))
        return minimum_var

    def is_consistent(self, var: Variable):
        for constraint in self.problem.constraints:
            if var in constraint.variables and not constraint.is_satisfied():
                return False
        return True

    def lcv(self, var: Variable):
        doamin_sorted = sorted(var.domain, key=lambda val: self.count_conflicts(var, val))
        return doamin_sorted

    def count_conflicts(self, var, val):
        conflicts = 0
        var.value = val
        for neighbor in var.neighbors:
            if (not neighbor.has_value):
                for other_var_candidate in neighbor.domain:
                    neighbor.value = other_var_candidate
                    if (not self.is_consistent(var)):
                        conflicts += 1
                    neighbor.value = None

        var.value = None
        return conflicts

    def create_domain_snapshot(self):  # Creating a snapshot of domains before forward checking
        domain_snapshots = {}
        for variable in self.problem.variables:
            if (not variable.has_value):
                domain_snapshots[variable] = variable.domain[:]
        return domain_snapshots
