def load(grid_file, grid_type='p'):
    import numpy as np
    import xarray as xr
    """
    Load grid data of BLOM.

    Args:
        grid_file (str): Path to the grid file.
        grid_type (str): Grid type (e.g., 'p').

    Returns:
        tuple: Latitude, longitude, depth, mask and extended vertices (clat, clon).
    """
    with xr.open_dataset(grid_file) as grid:
        lat = grid[grid_type + 'lat'].data
        lon = grid[grid_type + 'lon'].data
        clat = grid[grid_type + 'clat'].data
        clon = grid[grid_type + 'clon'].data
        mask= grid[grid_type + 'mask'].data
        depth= grid[grid_type + 'depth'].data

    dims = [x + 1 for x in list(lat.shape)]
    clat_new = np.zeros(dims)
    clon_new = np.zeros(dims)
    clat_new[:-1, :-1] = clat[0, :, :]  # lower-left patch
    clat_new[0:-1, -1] = clat[1, :, -1] # last column
    clat_new[-1, 0:-1] = clat[3, -1, :] # last row
    clat_new[-1, -1] = clat[2, -1, -1]  # upper-right corner

    clon_new[:-1, :-1] = clon[0, :, :]
    clon_new[0:-1, -1] = clon[1, :, -1]
    clon_new[-1, 0:-1] = clon[3, -1, :]
    clon_new[-1, -1] = clon[2, -1, -1]

    return lat, lon, depth, mask, clat_new, clon_new

def corners_to_vertices(c):
    import numpy as np
    """(nv=4, y, x) cell corners [SW, SE, NE, NW] -> (y+1, x+1) grid vertices."""
    ny, nx = c.shape
    v = np.empty((ny + 1, nx + 1), dtype=c.dtype)
    v[:-1, :-1] = c[0]        # SW corner of every cell
    v[:-1, -1] = c[1][:, -1]  # SE corner of the easternmost column
    v[-1, :-1] = c[2][-1, :]  # NE corner of the northernmost row
    v[-1, -1] = c[2][-1, -1]
    return v

def read_strait_indices(filename, strait_name):
    """
    Read a text data file and return indices/flags for a given strait section.

    Parameters
    ----------
    filename : str
        Path to the text data file.
    strait_name : str
        Name of the strait section (e.g. "florida_bahamas_strait").

    Returns
    -------
    i_index : list[int]
        First column (i-index).
    j_index : list[int]
        Second column (j-index).
    uflag : list[int]
        Third column.
    vflag : list[int]
        Fourth column.
    """
    i_index, j_index, uflag, vflag = [], [], [], []
    current = None

    with open(filename, "r") as f:
        for line in f:
            stripped = line.strip()
            if not stripped:
                continue

            # Section header
            if stripped.lower().startswith("name:"):
                current = stripped.split(":", 1)[1].strip()
                continue

            # Data lines only for the requested strait
            if current == strait_name:
                parts = stripped.split()
                if len(parts) != 4:
                    raise ValueError(
                        f"Expected 4 columns, got {len(parts)} in line: {stripped!r}"
                    )
                try:
                    a, b, c, d = (int(p) for p in parts)
                except ValueError:
                    raise ValueError(f"Non-integer value in line: {stripped!r}")
                i_index.append(a)
                j_index.append(b)
                uflag.append(c)
                vflag.append(d)

    if not i_index:
        raise ValueError(f"Strait section {strait_name!r} not found in {filename!r}")

    return i_index, j_index, uflag, vflag
