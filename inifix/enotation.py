import re

ENOTATION_REGEXP = re.compile(r"\d+(\.\d*)?e[+-]?\d+?")


class ENotationIO:
    """A small class to encode/decode real numbers to and from
    e-notation formatted strings.

    """

    @staticmethod
    def decode(s, /):
        """
        Cast an 'e' formatted string `s` to integer if such a conversion can
        be perfomed without loss of data. Raise ValueError otherwise.

        Examples
        --------
        >>> ENotationIO.decode("6.28E2")
        628
        >>> ENotationIO.decode("1.4e3")
        1400
        >>> ENotationIO.decode("7.0000E2")
        700
        >>> ENotationIO.decode("700.00E-2")
        7
        >>> ENotationIO.decode("700e-2")
        7
        >>> ENotationIO.decode("6.000e0")
        6
        >>> ENotationIO.decode("700e-3")
        Traceback (most recent call last):
        ...
        ValueError
        >>> ENotationIO.decode("7.0001E2")
        Traceback (most recent call last):
        ...
        ValueError
        >>> ENotationIO.decode("0.6e0")
        Traceback (most recent call last):
        ...
        ValueError

        """
        s = s.lower()  # assuming Idefix knows how to read "1e3" as well as "1E3"

        if not re.match(ENOTATION_REGEXP, s):
            raise ValueError

        digits, exponent = s.split("e")
        exponent = int(exponent)
        if "." in digits:
            digits, decimals = digits.split(".")
            decimals = decimals.rstrip("0")
        else:
            decimals = ""

        if exponent >= 0 and len(decimals) > exponent:
            raise ValueError
        elif exponent < 0 and len(digits) - 1 < -exponent:
            raise ValueError

        return int(float(s))

    @staticmethod
    def simplify(s: str, /):
        """
        Simplify exponents and trailing zeros in decimals.
        This is a helper function to `ENotationIO.encode`.

        >>> ENotationIO.simplify('1e-00')
        '1e0'
        >>> ENotationIO.simplify('1e+00')
        '1e0'
        >>> ENotationIO.simplify('1e-01')
        '1e-1'
        >>> ENotationIO.simplify('1e+01')
        '1e1'
        >>> ENotationIO.simplify('1e+10')
        '1e10'
        >>> ENotationIO.simplify('1.000e+00')
        '1e0'
        >>> ENotationIO.simplify('1.100e+00')
        '1.1e0'
        """
        s = re.sub(r"\.?0*(e[+-]?)0", r"\1", s)
        s = re.sub(r"(e-0)$", "e0", s)
        return s.replace("+", "")

    @staticmethod
    def encode(r, /):
        """
        Convert a real number `r` to string, using scientific notation.

        Note that this differs from using format specifiers (e.g. `.6e`)
        in that trailing zeros are removed.
        Precision must be conserved.

        Parameters
        ----------
        r: real number (float or int)

        Returns
        -------
        ret: str
            A string representing a number in sci notation.

        Examples
        --------
        >>> ENotationIO.encode(1)
        '1e0'
        >>> ENotationIO.encode(0.0000001)
        '1e-7'
        >>> ENotationIO.encode(10_000_000)
        '1e7'
        >>> ENotationIO.encode(156_000)
        '1.56e5'
        >>> ENotationIO.encode(0.0056)
        '5.6e-3'
        >>> ENotationIO.encode(3.141592653589793)
        '3.141592653589793e0'
        >>> ENotationIO.encode(1e-15)
        '1e-15'
        >>> ENotationIO.encode(0.0)
        '0'
        >>> ENotationIO.encode(0)
        '0'
        """
        base = str(r)
        if "e" in base:
            return ENotationIO.simplify(base)
        if not base.strip(".0"):
            return "0"
        max_ndigit = len(base.replace(".", "")) - 1
        fmt = ".{}e".format(max_ndigit)
        s = "{:^{}}".format(r, fmt)
        return ENotationIO.simplify(s)

    @staticmethod
    def encode_preferential(r, /):
        """
        Convert a real number `r` to string, using sci notation if
        and only if it saves space.

        Examples
        --------
        >>> ENotationIO.encode_preferential(189_000_000)
        '1.89e8'
        >>> ENotationIO.encode_preferential(189)
        '189'
        >>> ENotationIO.encode_preferential(900)
        '900'
        >>> ENotationIO.encode_preferential(1)
        '1'
        >>> ENotationIO.encode_preferential(0.7)
        '0.7'
        >>> ENotationIO.encode_preferential(0.00007)
        '7e-5'
        """
        return min(str(r), ENotationIO.encode(r), key=lambda x: len(x))
