from math import log, floor

from deephyper.search.models.parameter import Parameter
from deephyper.search.models.types.steptype import StepType
from deephyper.search.models.types.parametertype import ParameterType
from deephyper.search.models.types.discreterepresentationtype import DiscreteRepresentationType

class DiscreteParameter(Parameter):
    """
    A class to describe a hyperparameter that takes discrete values
    on a numerical interval.
    """

    def __init__(self, name, low, high, step_type=StepType.ARITHMETIC,
                 step_size=1, repr_type=DiscreteRepresentationType.DEFAULT,
                 is_negative=False):
        """
        Keyword arguments:
        name -- A string to identify the parameter.
        low -- The lower bound of the interval on which the parameter
               takes values (inclusive).
        high -- The upper bound of the interval on which the parameter
                takes values (inclusive).
        step_type -- A `StepType` that specifies the way in which the
                     parameter's interval is traversed, e.g. arithmetic.
        step_size -- The magnitude of each step taken on the parameter's
                    interval.
        repr_type -- A `DiscreteRepresentationType` that specifies how
                     the parameter should be presented to a hyperparameter
                     optimizers.
        is_negative -- If the values on the discrete interval are negative.
        """
        # Implementation note: For geometric parameters with negative intervals,
        # it is easier to invert the interval.
        # E.g. [-8, -4, -2, -1] has step size 0.5, but we prefer to specify
        # the interval as [1, 2, 4, 8] with step size 2 and adding negative
        # signs where necessary via `is_negative`.
        self.low = low
        self.high = high
        self.step_type = step_type
        self.step_size = step_size
        self.repr_type = repr_type
        self.is_negative = is_negative
        super(DiscreteParameter, self).__init__(name, ParameterType.DISCRETE)

    # Provide a convenient way to output information about the parameter.
    def __str__(self):
        return ("<param n: \'{0}\', t: {1}, low: {2}, high: {3}, step_t: {4}, "
               "step_s: {5}, repr_t: {6}, is_neg: {7}>".format(
                self.name, self.type, self.low, self.high, self.step_type,
                self.step_size, self.repr_type, self.is_negative))

    def __repr__(self):
        return self.__str__()

    def interval_list(self):
        """
        Return a list of values that are on the discrete interval
        of the parameter.
        """
        # Unpack values for frequent loop reference.
        high = self.high
        is_neg = self.is_negative
        step_type = self.step_type
        step_size = self.step_size
        values = list()
        value_cur = self.low

        # Step through each value on the discrete interval and add it to
        # the values list.
        while value_cur <= high:
            # Add current value to values.
            if is_neg:
                values.append(-value_cur)
            else:
                values.append(value_cur)
            # Step to next value on the interval.
            if step_type == StepType.ARITHMETIC:
                value_cur += step_size
            elif step_type == StepType.GEOMETRIC:
                value_cur *= step_size

        return values

    # Implementation note: The approach of defining the function
    # 'map_to_interval` to map {0, 1, 2, 3, ..., n_max} to the parameter's
    # interval could be replaced by storing a list of the values on the
    # parameter's interval and using the non-negative sequence
    # {0, 1, ..., n_max} to index the list. This approach would require more
    # memory, and would still yield a constant time algorithim.
    # Thus the 'map_to_interval' approach was chosen.
    def map_to_interval(self, n):
        """Return the nth value on the parameter's interval (0-indexed)."""
        if self.step_type == StepType.ARITHMETIC:
            abs_val = self.low + (self.step_size * n)
        elif self.step_type == StepType.GEOMETRIC:
            abs_val = self.low * (self.step_size ** n)

        if self.is_neg:
            return -abs_val
        else:
            return abs_val

    def max_n(self):
        """
        Return the greatest n, element of the naturals, such that:
            Arithmetic: lower_bound + (step_size * n) <= upper_bound.
            Geometric:  lower_bound * (step_size ^ n) <= upper_bound.
        i.e. what is the largest value that should be passed to map_to_interval?
        """
        # Unpack and cast parameter values for correct arithmetic.
        low = float(self.low)
        high = float(self.high)
        step_size = float(self.step_size)

        # Compute max n.
        if self.step_type == StepType.ARITHMETIC:
            n = int(floor((high - low) / step_size))
            # Correct for roundoff error.
            if (n * step_size + low) <= (high - step_size):
                return n + 1
            else:
                return n
        elif self.step_type == StepType.GEOMETRIC:
            if lower_bound < 0:
                n = int(floor(log(low / high, step_size)))
                # Correct for roundoff error.
                if(low / (step_size ** n) <= high * step_size):
                    return n + 1
                else:
                    return n
            else:
                n = int(floor(log(high / low, step_size)))
                # Correct for roundoff error.
                if (low * (step_size ** n)) <= (high / step_size):
                    return n + 1
                else:
                    return n

    # Ensure the parameter was constructed properly.
    def debug(self):
        """Ensure that the parameter's construction was well-formed."""
        super(DiscreteParameter, self).debug()

        # Ensure valid step type.
        if not isinstance(self.step_type, StepType):
            raise Warning("Parameter constructed with unrecognized step "
                          "type: {0}".format(self))

        # Ensure valid representation type.
        if not isinstance(self.repr_type, DiscreteRepresentationType):
            raise Warning("Parameter constructed with unrecognized "
                          "representation type: {0}".format(self))

        # Ensure the interval has valid lower and upper bounds.
        if self.low < 0:
            raise Warning("Discrete parameter constructed with negative lower "
                          "bound. Please make use of the `is_negative` "
                          "constructor argument. {0}".format(self))

        if self.low >= self.high:
            raise Warning("Parameter's lower bound exceeds or is equal to "
                          "to its upper bound: {0}".format(self))

        # Ensure a valid step size was given.
        if self.step_size <= 0:
            raise Warning("Parameter constructed with step size less than "
                          "or equal to 0: {0}".format(self))

        if (self.step_type == StepType.GEOMETRIC
                and self.step_size <= 1):
            raise Warning("Parameter has geometric step type and step size <= "
                          "1: {0}".format(self))

        # Check for miscellaneous inconsistencies.
        # Ensure the upper and lower bounds of a discrete, geometric parameter
        # are not zero and that the signs of the bounds match.
        if self.step_type == StepType.GEOMETRIC:
            if self.low == 0 or self.high == 0:
                raise Warning("Parameter has geometric step type and a bound "
                              "of 0 on its interval: {0}".format(self))
            if ((self.low < 0 and self.high > 0)
                    or (self.low > 0 and self.high < 0)):
                raise Warning("Parameter has geometric step type and its "
                              "bounds have different sign: {0}".format(self))

        return