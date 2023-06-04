import tqdm

DEFAULT_BAR_FORMAT = {
    'simple': '| {desc} - {elapsed} < {remaining}',
    'qurry-full': '| {n_fmt}/{total_fmt} {percentage:3.0f}%|{bar}| - {desc} - {elapsed} < {remaining}',
    'qurry-barless': '| {n_fmt}/{total_fmt} - {desc} - {elapsed} < {remaining}',
}
PROGRESSBAR_ASCII = {
    '4squares': " ▖▘▝▗▚▞█",
    'standard': " ▏▎▍▌▋▊▉█",
    'decimal': " 123456789#",
    'braille': " ⠏⠛⠹⠼⠶⠧⠿",
    'boolen-eq': " =",
}


class qurryProgressBar(tqdm.tqdm):

    @staticmethod
    def default_setup(
        bar_format: str = 'qurry-full',
        ascii: str = '4squares',
    ) -> dict[str, str]:
        if bar_format in DEFAULT_BAR_FORMAT:
            actual_bar_format = DEFAULT_BAR_FORMAT[bar_format]
        else:
            actual_bar_format = bar_format

        if ascii in PROGRESSBAR_ASCII:
            actual_ascii = PROGRESSBAR_ASCII[ascii]
        else:
            actual_ascii = ascii

        return {
            'bar_format': actual_bar_format,
            'ascii': actual_ascii,
        }

    def __init__(
        self,
        *args,
        bar_format: str = 'qurry-full',
        ascii: str = '4squares',
        **kwargs,
    ):
        result_setup = self.default_setup(bar_format, ascii)
        self.actual_bar_format = result_setup['bar_format']
        self.actual_ascii = result_setup['ascii']

        super().__init__(
            *args,
            bar_format=self.actual_bar_format,
            ascii=self.actual_ascii,
            **kwargs
        )
