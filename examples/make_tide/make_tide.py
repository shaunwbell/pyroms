'''
this is an example to generate a ROMS tide file for TPXO8-atlas tidal product. Till this moment I couldn't found
a good python script to do so, so this script is created for this purpose. TPXO8-atlas is a high resolution global
model of ocean tides. it is available here:

http://volkov.oce.orst.edu/tides/tpxo8_atlas.html

download the 8 major constitutes with 1/30 deg resotuion. Other constitutes are also supported, but haven't been
tested. Only netCDF format is supported in this version, so make sure you download the right files.

The script 'make_remap_weights_file.py' is used to generate weight file between two grids, in this example the
Glacier Bay and TPXO8 grid files. TPXO8 grid file is kept in the same directory as data files:

/Volumes/R1/scratch/chuning/data/tpxo8nc/grid_tpxo8atlas_30_v1.nc

Run this script before 'make_tide.py' to generate the weight files (remap_*.nc).

To use the remap function a new set of grid is created (CGrid_TPXO8). I followed the structure of GLORY CGrid 
from the PYROMS packaage itself, so that it is consistent with PYROMS.

---------------------------------------------------------------------------------------------------------------------
tidal parameters are converted to elliptical parameters using ap2ep, origionally written in MATLAB and later
translated to python package PyFVCOM. See

CGrid_TPXO8/tidal_ellipse.py for more details.

-Chuning Wang, Dec 18 2016

'''

import netCDF4 as nc
import numpy as np
from scipy.interpolate import griddata

import pyroms
import pyroms_toolbox

import CGrid_TPXO8

# tidal constituents
consts =['Q1', 'O1', 'O1', 'K1', 'N2', 'M2', 'S2', 'K2'] 
# consts =['M2'] 
consts_num = len(consts)

# read roms grid
dst_grd = pyroms.grid.get_ROMS_grid('GB')
lat = dst_grd.hgrid.lat_rho
lon = dst_grd.hgrid.lon_rho
eta, xi = lat.shape

# read weights file
wts_file_t = 'remap_weights_TPXO8_to_GlacierBay_bilinear_t_to_rho.nc' 
wts_file_u = 'remap_weights_TPXO8_to_GlacierBay_bilinear_u_to_rho.nc' 
wts_file_v = 'remap_weights_TPXO8_to_GlacierBay_bilinear_v_to_rho.nc' 

# read TPXO8 files
pth_tpxo = "/Volumes/R1/scratch/chuning/data/tpxo8nc/"
srcgrd = CGrid_TPXO8.get_nc_CGrid_TPXO8(pth_tpxo+"grid_tpxo8atlas_30_v1.nc")
dstgrd = pyroms.grid.get_ROMS_grid('GB')

# grid sub-sample
xrange = srcgrd.xrange
yrange = srcgrd.yrange

# initiate variables
hamp = np.zeros((consts_num, eta, xi))*np.nan
hpha = np.zeros((consts_num, eta, xi))*np.nan
cmax = np.zeros((consts_num, eta, xi))*np.nan
cmin = np.zeros((consts_num, eta, xi))*np.nan
cang = np.zeros((consts_num, eta, xi))*np.nan
cpha = np.zeros((consts_num, eta, xi))*np.nan

k = -1
for cst in consts:
    k = k+1

    fid = nc.Dataset(pth_tpxo+'hf.'+cst.lower()+'_tpxo8_atlas_30c_v1.nc', 'r')
    hRe = fid.variables['hRe'][yrange[0]:yrange[1]+1, xrange[0]:xrange[1]+1]
    hIm = fid.variables['hIm'][yrange[0]:yrange[1]+1, xrange[0]:xrange[1]+1]
    fid.close()

    fid = nc.Dataset(pth_tpxo+'uv.'+cst.lower()+'_tpxo8_atlas_30c_v1.nc', 'r')
    uRe = fid.variables['uRe'][yrange[0]:yrange[1]+1, xrange[0]:xrange[1]+1]
    uIm = fid.variables['uIm'][yrange[0]:yrange[1]+1, xrange[0]:xrange[1]+1]
    vRe = fid.variables['vRe'][yrange[0]:yrange[1]+1, xrange[0]:xrange[1]+1]
    vIm = fid.variables['vIm'][yrange[0]:yrange[1]+1, xrange[0]:xrange[1]+1]
    fid.close()

    hRe = hRe*1.0
    hIm = hIm*1.0
    uRe = uRe*1.0
    uIm = uIm*1.0
    vRe = vRe*1.0
    vIm = vIm*1.0

    # unit convertion
    hRe = hRe/1000.  # mm to m
    hIm = hIm/1000.  # mm to m
    uRe = uRe/10000.  # cm2s-1 to m2s-1
    uIm = uIm/10000.  # cm2s-1 to m2s-1
    vRe = vRe/10000.  # cm2s-1 to m2s-1
    vIm = vIm/10000.  # cm2s-1 to m2s-1

    # convert vertical transport (uRe, vRe) to velocity
    uRe = uRe/srcgrd.z_u  # ms-1
    uIm = uIm/srcgrd.z_u  # ms-1
    vRe = vRe/srcgrd.z_v  # ms-1
    vIm = vIm/srcgrd.z_v  # ms-1

    # mask invalid data
    hRe = np.ma.masked_where(~srcgrd.mask_t, hRe)
    hIm = np.ma.masked_where(~srcgrd.mask_t, hIm)
    uRe = np.ma.masked_where(~srcgrd.mask_u, uRe)
    uIm = np.ma.masked_where(~srcgrd.mask_u, uIm)
    vRe = np.ma.masked_where(~srcgrd.mask_v, vRe)
    vIm = np.ma.masked_where(~srcgrd.mask_v, vIm)

    # remap h, u, v
    hRe = pyroms.remapping.remap(hRe, wts_file_t, spval=srcgrd.missing_value)
    hIm = pyroms.remapping.remap(hIm, wts_file_t, spval=srcgrd.missing_value)
    uRe = pyroms.remapping.remap(uRe, wts_file_u, spval=srcgrd.missing_value)
    uIm = pyroms.remapping.remap(uIm, wts_file_u, spval=srcgrd.missing_value)
    vRe = pyroms.remapping.remap(vRe, wts_file_v, spval=srcgrd.missing_value)
    vIm = pyroms.remapping.remap(vIm, wts_file_v, spval=srcgrd.missing_value)

    hamp[k, :, :] = (hRe**2+hIm**2)**0.5  # mm
    hpha[k, :, :] = np.arctan(-hIm/hRe)/np.pi*180.  # deg
    uamp = (uRe**2+uIm**2)**0.5  # mm
    upha = np.arctan(-uIm/uRe)/np.pi*180.  # deg
    vamp = (vRe**2+vIm**2)**0.5  # mm
    vpha = np.arctan(-vIm/vRe)/np.pi*180.  # deg


    # convert ap to ep
    cmax[k, :, :], ecc, cang[k, :, :], cpha[k, :, :], w = CGrid_TPXO8.tidal_ellipse.ap2ep(uamp, upha, vamp, vpha)
    cmin[k, :, :] = cmax[k, :, :]*ecc

# -------------------------------------------------------------------------
# mask land grid points
cmax[:, dstgrd.hgrid.mask_rho==0] = srcgrd.missing_value
cmin[:, dstgrd.hgrid.mask_rho==0] = srcgrd.missing_value
cang[:, dstgrd.hgrid.mask_rho==0] = srcgrd.missing_value
cpha[:, dstgrd.hgrid.mask_rho==0] = srcgrd.missing_value

# -------------------------------------------------------------------------
savedata = 1
if savedata == 1:
    # write tidal information to nc file
    # -------------------------------------------------------------------------
    # define tidal constituents names and periods
    tide_name = np.array([ list('Q1'), list('O1'), list('P1'), list('K1'),
                           list('N2'), list('M2'), list('S2'), list('K2')])
    tide_period = np.array([26.8683567047119, 25.8193397521973, 24.0658893585205, 23.9344692230225, 
                            12.6583499908447, 12.420599937439, 12, 11.9672346115112])

    # -------------------------------------------------------------------------
    # create nc file
    fh = nc.Dataset('../../data/GB_tides_otps.nc', 'w')
    fh.createDimension('namelen', 4)
    fh.createDimension('tide_period', 8)
    fh.createDimension('eta_rho', eta)
    fh.createDimension('xi_rho', xi)


    fh.history = 'Tides from TPXO8'
    import time
    fh.creation_date = time.strftime('%c')
    fh.type = 'Forcing File'


    name_nc = fh.createVariable('tide_name', 'c', ('tide_period', 'namelen'))

    period_nc = fh.createVariable('tide_period', 'd', ('tide_period'), fill_value=-9999)
    period_nc.field = 'tide_period, scalar'
    period_nc.long_name = 'tidal angular period'
    period_nc.units = 'hours'


    Eamp_nc = fh.createVariable('tide_Eamp', 'd', ('tide_period', 'eta_rho', 'xi_rho'), fill_value=-9999)
    Eamp_nc.field = 'tide_Eamp, scalar'
    Eamp_nc.long_name = 'tidal elevation amplitude'
    Eamp_nc.units = 'meter'

    Ephase_nc = fh.createVariable('tide_Ephase', 'd', ('tide_period', 'eta_rho', 'xi_rho'), fill_value=-9999)
    Ephase_nc.field = 'tide_Ephase, scalar'
    Ephase_nc.long_name = 'tidal elevation phase angle'
    Ephase_nc.units = 'degrees, time of maximum elevation with respect chosen time orgin'

    Cmax_nc = fh.createVariable('tide_Cmax', 'd', ('tide_period', 'eta_rho', 'xi_rho'), fill_value=-9999)
    Cmax_nc.field = 'tide_Cmax, scalar'
    Cmax_nc.long_name = 'maximum tidal current, ellipse semi-major axis'
    Cmax_nc.units = 'meter second-1'

    Cmin_nc = fh.createVariable('tide_Cmin', 'd', ('tide_period', 'eta_rho', 'xi_rho'), fill_value=-9999)
    Cmin_nc.field = 'tide_Cmin, scalar'
    Cmin_nc.long_name = 'minimum tidal current, ellipse semi-minor axis'
    Cmin_nc.units = 'meter second-1'

    Cangle_nc = fh.createVariable('tide_Cangle', 'd', ('tide_period', 'eta_rho', 'xi_rho'), fill_value=-9999)
    Cangle_nc.field = 'tide_Cangle, scalar'
    Cangle_nc.long_name = 'tidal current inclination angle'
    Cangle_nc.units = 'degrees between semi-major axis and East'

    Cphase_nc = fh.createVariable('tide_Cphase', 'd', ('tide_period', 'eta_rho', 'xi_rho'), fill_value=-9999)
    Cphase_nc.field = 'tide_Cphase, scalar'
    Cphase_nc.long_name = 'tidal current phase angle'
    Cphase_nc.units = 'degrees, time of maximum velocity'

    # -------------------------------------------------------------------------
    # write data
    name_nc[:, 0:2] = tide_name
    period_nc[:] = tide_period

    Eamp_nc[:, :, :] = hamp
    Ephase_nc[:, :, :] = hpha
    Cmax_nc[:, :, :] = cmax
    Cmin_nc[:, :, :] = cmin
    Cangle_nc[:, :, :] = cang
    Cphase_nc[:, :, :] = cpha

    fh.close()

