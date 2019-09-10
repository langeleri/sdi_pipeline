"""
align -- this module aligns sets of astronomical data
HISTORY
    Created/Substantially refactored on 2019-09-01
        Varun Iyer <varun_iyer@ucsb.edu>
"""
# general imports
import numpy as np
# types
from ..common import to_np, HDU_TYPES
from astropy.io.fits import PrimaryHDU
from .ref_image import ref_image
from ..sources import Source

UNABLE = "Unable to find {} module(s); {} alignment method is disabled."
# for astroalign method
try:
    import astroalign
except ImportError:
    print(UNABLE.format("astroalign", "astroalign"))
# for skimage method
try:
    from skimage.feature import register_translation
    from scipy.ndimage import fourier_shift
except ImportError:
    print(UNABLE.format("skimage or scipy", "skimage"))
# for chi2 method
try:
    from image_registration import chi2_shift
    from image_registration import fft_tools
except ImportError:
    print(UNABLE.format("image_registration", "chi2"))
# for imreg method
try:
    import imreg_dft
except ImportError:
    print(UNABLE.format("imreg_dft", "imreg"))


DISABLED = "Alignment method {} is disabled because the {} module(s) is/are not installed."


def align(source_s, reference=None, method="astroalign"):
    """
    Aligns the source astronomical image(s) to the reference astronomical image
    ARGUMENTS
        source_s -- the image(s) to align; fitsio HDU object, numpy array,
            or a list of either one of the above
    KEYWORD ARGUMENTS
        reference -- the image against which to align the source image;
            fitsio HDU object or numpy array. If None, the best option is chosen
            from among the sources.
        method -- the library to use to align the images. options are:
            astroalign (default), skimage, imreg, skimage, chi2
    RETURNS
        a transformed copy of the source image[s] in the same data type
        which was passed in
    """
    # make sure that we can handle source as a list
    sources = []
    outputs = []
    if isinstance(source_s, list):
        sources = source_s
    else:
        sources.append(source_s)

    if reference is None:
        reference = ref_image(sources)
    np_ref = to_np(reference, "Cannot align to unexpected type {}; expected numpy array or FITS HDU")

    for source in sources:
        np_src = to_np(source, "Cannot align unexpected type {}; expected numpy array or FITS HDU")
        # possibly unneccessary but unsure about scoping
        output = np.array([])

        if method == "astroalign":
            try:
                output = astroalign.register(np_src, np_ref)[0]
            except NameError:
                raise ValueError(DISABLED.format(method, "astroalign"))
        elif method == "skimage":
            try:
                shift = register_translation(np_ref, np_src, 100)[0]
                output_fft = fourier_shift(np.fft.fftn(np_src), shift)
                output = np.fft.ifftn(output_fft)
            except NameError:
                raise ValueError(DISABLED.format(method, "scipy or numpy"))
        elif method == "chi2":
            try:
                dx, dy = chi2_shift(np_ref, np_src, upsample_factor='auto')[:2]
                output = fft_tools.shift.shiftnd(data, (-dx, -dy))
            except NameError:
                raise ValueError(DISABLED.format(method, "image_registration"))
        elif method == "imreg":
            try:
                output = imreg_dft.similarity(np_ref, np_src)["timg"]
            except NameError:
                raise ValueError(DISABLED.format(method, "imreg_dft"))
        else:
            raise ValueError("Unexpected alignment method {}!".format(method))

        if isinstance(source, HDU_TYPES):
            output = PrimaryHDU(output, source.header)
        outputs.append(output)

    return outputs if isinstance(source_s, list) else outputs[0]

 
def sources(catalogs, reference=None):
    """
    Takes a list of HDU catalogs and calculates an alignment
    Returns a list of lists of transformed Source objects
    Arguments:
        catalogs -- list of catalogs
    Keyword Arguments:
        reference -- A set of points to use as a reference; default 0th index
    """
    # FIXME this is really slow, move to Cython or do some numpy magic with
    # Sources class
    aligned = []
    if reference is None:
        reference = catalogs[0]
    npref = [[r["X"], r["Y"]] for r in reference.data]
    for cat in catalogs:
        npc = [[c["X"], c["Y"]] for c in cat.data]
        c_align = []
        T, _ = astroalign.find_transform(npc, npref)
        for source in cat.data:
            s = Source(source, dtype=cat.data.dtype)
            s.transform(T)
            c_align.append(s)
        aligned.append(c_align)
    return aligned
