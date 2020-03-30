# Python 3.5
# Script written by Kayla Iacovino (kayla.iacovino@nasa.gov)
# VERSION 0.1- MARCH 2020

import pandas as pd
import numpy as np
from thermoengine import equilibrate
import matplotlib.pyplot as plt

#----------DEFINE SOME CONSTANTS-------------#
oxides = ['SiO2', 'TiO2', 'Al2O3', 'Fe2O3', 'Cr2O3', 'FeO', 'MnO', 'MgO', 'NiO', 'CoO', 'CaO', 'Na2O', 'K2O', 'P2O5', 
		  'H2O', 'CO2']
oxideMass = {'SiO2':28.085+32,'MgO':24.305+16,'FeO':55.845+16,'CaO':40.078+16,'Al2O3':2*26.982+16*3,'Na2O':22.99*2+16,
             'K2O':39.098*2+16,'MnO':54.938+16,'TiO2':47.867+32,'P2O5':2*30.974+5*16,'Cr2O3':51.996*2+3*16,
             'NiO':58.693+16, 'CoO':28.01+16, 'Fe2O3':55.845*2+16*3,
             'H2O':18.02, 'CO2':44.01}
CationNum = {'SiO2':1,'MgO':1,'FeO':1,'CaO':1,'Al2O3':2,'Na2O':2,
             'K2O':2,'MnO':1,'TiO2':1,'P2O5':2,'Cr2O3':2,
             'NiO':1,'CoO':1,'Fe2O3':2,'H2O':2, 'CO2':1}
CationCharge = {'SiO2':4,'MgO':2,'FeO':2,'CaO':2,'Al2O3':3,'Na2O':1,
             'K2O':1,'MnO':2,'TiO2':4,'P2O5':5,'Cr2O3':3,
             'NiO':2,'CoO':2,'Fe2O3':3,'H2O':1, 'CO2':4}
CationMass = {'SiO2':28.085,'MgO':24.305,'FeO':55.845,'CaO':40.078,'Al2O3':26.982,'Na2O':22.990,
             'K2O':39.098,'MnO':54.938,'TiO2':47.867,'P2O5':30.974,'Cr2O3':51.996,
             'NiO':58.693,'CoO':28.01,'Fe2O3':55.845,'H2O':2, 'CO2':12.01}

#----------DEFINE SOME EXCEPTIONS--------------#
class Error(Exception):
    """Base class for exceptions in this module."""
    pass

class InputError(Error):
    """Exception raised for errors in the input.

    Attributes:
        expression -- input expression in which the error occurred
        message -- explanation of the error
    """

    def __init__(self, message):
        self.message = message

#----------DEFINE SOME BASIC METHODS-----------#
def mol_to_wtpercent(dataframe):
	"""
	Takes in a pandas DataFrame containing multi-sample input and returns a pandas DataFrame object 
	with oxide values converted from mole percent to wt percent.

	Parameters
	----------
	dataframe: pandas DataFrame object
		Variable name referring to the pandas DataFrame object that contains user-imported data
	"""
	data = dataframe

	for key, value in oxideMass.items():
		data.loc[:,key] *= value 

	data["MPOSum"] = sum([data[oxide] for oxide in oxides])

	for oxide in oxides:
		data.loc[:,oxide] /= data['MPOSum']
		data.loc[:,oxide] *= 100
	del data['MPOSum']

	return data


#------------DEFINE MAJOR CLASSES-------------------#
class ExcelFile(object):
	"""An excel file with sample names and oxide compositions

	Attributes
	----------
		input_type: str
			String defining whether the oxide composition is given in wt percent ("wtpercent", which is the default),
			mole percent ("molpercent"), or mole fraction ("molfrac).
	"""

	def __init__(self, filename, input_type='wtpercent'):
		"""Return an ExcelFile object whoes parameters are defined here."""
		self.input_type = input_type

		data = pd.read_excel(filename)

		try:
			data = data.set_index('Label')
		except:
			raise InputError("Imported file must contain a column of sample names with the column name \'Label\'")

		for oxide in oxides:
			if oxide in data.columns:
				pass
			else:
				data[oxide] = 0.0

		#TODO test all input types produce correct values
		if input_type == "wtpercent":
			pass

		if input_type == "molpercent":
			data = mol_to_wtpercent(data)

		if input_type == "molfrac":
			data = mol_to_wtpercent(data)

		self.data = data

	def get_sample_oxide_comp(self, sample):
		"""
		Returns oxide composition of a single sample from a user-imported excel file as a dictionary

		Parameters
		----------
		sample: string
			Name of the desired sample

		Returns
		-------
		dictionary
			Composition of the sample as oxides
		"""
		sample = sample
		data = self.data
		my_sample = pd.DataFrame(data.loc[sample])
		sample_dict = (my_sample.to_dict()[sample])
		sample_oxides = {}
		for item, value in sample_dict.items():
			if item in oxides:
				sample_oxides.update({item:value})
		return sample_oxides

class Modeller(object):
	"""An object with arguments describing the necessary parameters to instantiate a thermoengine equilibrate class:
	Attributes
	----------
		model_name: str 
			Name of desired model to instantiate.
			Options: MagmaSat, ...

		model_version: str 
			Version number of model desired. Only required if model_name is MagmaSat
	"""

	def __init__(self, model_name, model_version):
		"""Return a Modeller object whose parameters are defined here"""
		self.model_name = model_name
		self.model_version = model_version

		model_names = ['MagmaSat']

		try: 
			model_name in model_names
		except:
			raise InputError("Model name passed is not a recognized model.")

		if model_name == "MagmaSat":
			#instantiate thermoengine equilibrate MELTS instance
			melts = equilibrate.MELTSmodel(model_version)
			self.melts = melts

			#Suppress phases not required in the melts simulation
			self.oxides = melts.get_oxide_names()
			self.phases = melts.get_phase_names()

			for phase in self.phases:
			    melts.set_phase_inclusion_status({phase:False})
			    melts.set_phase_inclusion_status({'Fluid':True, 'Liquid':True})



	def calculate_isobars_and_isopleths(self, sample, temp, print_status=False, pressure_min='', pressure_max='', pressure_int='', pressure_list=''):
		"""
		Plots isobars and isopleths at a constant temperature for a given sample. Isobars can be calculated
		for any number of pressures. Pressures can be passed as min, max, interval (100.0, 500.0, 100.0 would result
		in pressures of 100.0, 200.0, 300.0, 400.0, and 500.0 MPa). Alternatively pressures can be passed as a list of all 
		desired pressures ([100.0, 200.0, 250.0, 300.0] would calculate isobars for each of those pressures in MPa).

		Parameters
		----------
		sample: dict
			Dictionary with values for sample composition as oxides in wt%.

		temp: float
			Temperature in degrees C.

		pressure_min: float
			OPTIONAL. If passed, also requires pressure_max and pressure_int be passed. If passed, do not pass
			pressure_list. Minimum pressure	value in MPa.

		pressure_max: float
			OPTIONAL. If passed, also requires pressure_min and pressure_int be passed. If passed, do not pass
			pressure_list. Maximum pressure value in MPa.

		pressure_int: float
			OPTIONAL: If passed, also requires pressure_min and pressure_max be passed. If passed, do not pass
			pressure_list. Interval between pressure values in MPa.

		pressure_list: list
			OPTIONAL: If passed, do not pass pressure_min, pressure_max, or pressure_int. List of all pressure 
			values in MPa.

		print_status: bool
			OPTIONAL: Default is False. If set to True, progress of the calculations will be printed to the terminal.

		Returns
		-------
		pandas DataFrame object
			DataFrame containing calcualted isobar and isopleth information for the passed melt composition. Column titles
			are 'Pressure', 'H2Omelt', 'CO2melt', 'H2Ofl', and 'CO2fl'.
		"""
		if isinstance(pressure_min,float) and isinstance(pressure_list,list):
			raise InputError("Enter pressure either as min, max, int OR as list. Not both.")
		if isinstance(pressure_max,float) and isinstance(pressure_list,list):
			raise InputError("Enter pressure either as min, max, int OR as list. Not both.")
		if isinstance(pressure_int,float) and isinstance(pressure_list,list):
			raise InputError("Enter pressure either as min, max, int OR as list. Not both.")

		if isinstance(pressure_min, float):
			P_vals = np.arange(pressure_min, pressure_max+pressure_int, pressure_int)

		if isinstance(pressure_list,list):
			P_vals = pressure_list

		bulk_comp = sample
		melts = self.melts
		phases = self.phases
		oxides = self.oxides
		phases = melts.get_phase_names()

		volatiles_at_saturation = []
		H2O_val = 0
		CO2_val = 0
		fluid_mass = 0.0

		#Calculate equilibrium phase assemblage for all P/T conditions, check if saturated in fluid...
		for i in P_vals:
		    if print_status==True:
		    	print("Calculating isobars at " + str(i) + " MPa")
		    
		    for j in np.arange(0, 15.5, 0.5):
		        bulk_comp["H2O"] = j
		        while fluid_mass <= 0.0: 
		            bulk_comp["CO2"] = CO2_val

		            melts.set_bulk_composition(bulk_comp)

		            output = melts.equilibrate_tp(temp, i, initialize=True)
		            (status, temp, i, xmlout) = output[0]
		            fluid_mass = melts.get_mass_of_phase(xmlout, phase_name='Fluid')

		            CO2_val = CO2_val + 0.1

		        if fluid_mass > 0.0:
		            liquid_comp = melts.get_composition_of_phase(xmlout, phase_name='Liquid', mode='oxide_wt')
		            fluid_comp = melts.get_composition_of_phase(xmlout, phase_name='Fluid')

		            if "H2O" in liquid_comp:
		                        H2O_liq = liquid_comp["H2O"]
		            else:
		                H2O_liq = 0

		            if "CO2" in liquid_comp:
		                CO2_liq = liquid_comp["CO2"]
		            else:
		                CO2_liq = 0

		            if "H2O" in fluid_comp:
		                H2O_fl = fluid_comp["H2O"]
		            else:
		                H2O_fl = 0.0
		            if "CO2" in fluid_comp:
		                CO2_fl = fluid_comp["CO2"]
		            else:
		                CO2_fl = 0.0
		            volatiles_at_saturation.append([i, H2O_liq, CO2_liq, H2O_fl, CO2_fl])
		            CO2_val = 0.0
		            fluid_mass = 0.0

		if print_status == True:
		    print("Done!")

		isobars_df = pd.DataFrame(volatiles_at_saturation, columns = ['Pressure', 'H2Omelt', 'CO2melt', 'H2Ofl', 'CO2fl'])

		return isobars_df

	def plot_isobars_and_isopleths(self, isobars_df):
		"""
		Takes in a dataframe with calculated isobar and isopleth information (e.g., output from calculate_isobars_and_isopleths)
		and plots data as isobars (lines of constant pressure) and isopleths (lines of constant fluid composition). These lines
		represent the saturation pressures of the melt composition used to calculate the isobar and isopleth information.

		Parameters
		----------
		isobars_df: pandas DataFrame
			DataFrame object containing isobar and isopleth information as calculated by calculate_isobars_and_isopleths.

		Returns
		-------
		matplotlib object
			Plot with x-axis as H2O wt% in the melt and y-axis as CO2 wt% in the melt. Isobars, or lines of
			constant pressure at which the sample magma composition is saturated, and isopleths, or lines of constant
			fluid composition at which the sample magma composition is saturated, are plotted.
		"""
		P_vals = isobars_df.Pressure.unique()
		isobars_lists = isobars_df.values.tolist()

		#make a list of isopleth values to plot
		iso_step = 20.0
		isopleth_vals = np.arange(0+iso_step,100.0,iso_step)

		#add zero values to volatiles list
		isobars_lists.append([0.0,0.0,0.0,0.0])

		#draw the figure
		fig, ax1 = plt.subplots()

		#turn on interactive plotting
		plt.ion()

		plt.xlabel('H2O wt%')
		plt.ylabel('CO2 wt%')

		#Plot some stuff
		for pressure in P_vals:
		    ax1.plot([item[1] for item in isobars_lists if item[0] == pressure], 
		             [item[2] for item in isobars_lists if item[0] == pressure])

		for val in isopleth_vals:
		    val_min = val-1.0
		    val_max = val+1.0
		    x_vals_iso = [item[1] for item in isobars_lists if val_min <= item[3] <= val_max]
		    x_vals_iso.append(0)
		    x_vals_iso = sorted(x_vals_iso)
		    x_vals_iso = np.array(x_vals_iso)
		    y_vals_iso = [item[2] for item in isobars_lists if val_min <= item[3] <= val_max]
		    y_vals_iso.append(0)
		    y_vals_iso = sorted(y_vals_iso)
		    y_vals_iso = np.array(y_vals_iso)
		    
		    ax1.plot(x_vals_iso, y_vals_iso, ls='dashed', color='k')

		labels = P_vals
		ax1.legend(labels)

		return ax1

	def calculate_saturation_pressure(self, sample, temp, print_status=False):
		"""
		Calculates the saturation pressure of one or more sample compositions, depending on what variable is passed to 'sample'.

		Parameters
		----------
		sample: dict or ExcelFile object
			Compositional information on one or more samples. A single sample can be passed as a dict or ExcelFile object.
			Multiple samples must be passed as an ExcelFile object.

		temp: float or str
			Temperature at which to calculate saturation pressures, in degrees C. Can be passed as float, in which case the 
			passed value is used as the temperature for all samples. Alternatively, temperature information for each individual
			sample may already be present in the passed ExcelFile object. If so, pass the str value corresponding to the column
			title in the passed ExcelFile object.

		print_status: bool
			OPTIONAL: Default is False. If set to True, progress of the calculations will be printed to the terminal.

		Returns
		-------
		pandas DataFrame object or dict
			If sample is passes as dict, dict is returned. If sample is passed as ExcelFile object, pandas DataFrame is
			returned. Values returned are saturation pressure in MPa, the mass of fluid present, and the composition of the
			fluid present.


		"""
		self.sample = sample
		self.temp = temp
		melts = self.melts
		oxides = self.oxides

		if isinstance(sample, dict):
			data = pd.DataFrame([v for v in sample.values()], 
                    index = [k for k in sample.keys()])
			data = data.transpose()
		elif isinstance(sample, ExcelFile):
			data = sample.data 
		else:
			raise InputError("sample must be type ExcelFile object or dict")

		if isinstance(temp, str):
			file_has_temp = True
		elif isinstance(temp, float):
			file_has_temp = False
		else:
			raise InputError("temp must be type str or float")

		#Do the melts equilibrations
		bulk_comp = {}
		startingP = []
		startingP_ref = []
		satP = []
		flmass = []
		flH2O = []
		flCO2 = []
		for index, row in data.iterrows():
		    bulk_comp = {oxide:  row[oxide] for oxide in oxides}
		    feasible = melts.set_bulk_composition(bulk_comp)
		    
		    if file_has_temp == True:
		        temp = row[temp]

		    fluid_mass = 0.0
		    press = 2000.0
		    while fluid_mass <= 0.0:
		        press -= 100.0
		        
		        output = melts.equilibrate_tp(temp, press, initialize=True)
		        (status, temp, i, xmlout) = output[0]
		        fluid_mass = melts.get_mass_of_phase(xmlout, phase_name='Fluid')
		        
		        if press <= 0:
		            break
		            
		    startingP.append(press+100.0)

		data["StartingP"] = startingP
		    
		for index, row in data.iterrows():
		    bulk_comp = {oxide:  row[oxide] for oxide in oxides}
		    feasible = melts.set_bulk_composition(bulk_comp)
		    
		    if file_has_temp == True:
		        temp = row[temp]
		    
		    fluid_mass = 0.0
		    press = row["StartingP"]
		    while fluid_mass <= 0.0:
		        press -= 10.0
		        
		        output = melts.equilibrate_tp(temp, press, initialize=True)
		        (status, temp, i, xmlout) = output[0]
		        fluid_mass = melts.get_mass_of_phase(xmlout, phase_name='Fluid')
		        
		        if press <= 0:
		            break
		            
		    startingP_ref.append(press+10.0)
		    
		data["StartingP_ref"] = startingP_ref
		    
		for index, row in data.iterrows():
		    bulk_comp = {oxide:  row[oxide] for oxide in oxides}
		    feasible = melts.set_bulk_composition(bulk_comp)
		    
		    if file_has_temp == True:
		        temp = row[temp]
		    
		    fluid_mass = 0.0
		    press = row["StartingP_ref"]
		    while fluid_mass <= 0.0:
		        press -= 1.0
		        
		        output = melts.equilibrate_tp(temp, press, initialize=True)
		        (status, temp, i, xmlout) = output[0]
		        fluid_mass = melts.get_mass_of_phase(xmlout, phase_name='Fluid')
		        
		        if press <= 0:
		            break
		            
		    satP.append(press)
		    flmass.append(fluid_mass)

		    flcomp = melts.get_composition_of_phase(xmlout, phase_name='Fluid')
		    flH2O.append(flcomp["H2O"])
		    flCO2.append(flcomp["CO2"])
		    
		    if print_status == True:
			    print (index)
			    print ("Pressure = " + str(press))
			    print ("Fluid mass = " + str(fluid_mass))
			    print ("\n")  


		data["SaturationPressure_MPa"] = satP
		data["FluidMassAtSaturation_grams"] = flmass
		data["H2Ofluid_wtper"] = flH2O
		data["CO2fluid_wtper"] = flCO2
		del data["StartingP"]
		del data["StartingP_ref"]

		if isinstance(sample, dict):
			data = data.transpose()
			data = data.to_dict()
			return data[0]
		elif isinstance(sample, ExcelFile):
			return data
                     

	def calculate_degassing_paths(self, sample, temp, system='open'):
		"""
		Calculates degassing path for one or more samples, depending on what variable is passed to 'sample'.

		Parameters
		----------
		sample: dict or ExcelFile object
			Compositional information on one or more samples. A single sample can be passed as a dict or ExcelFile object.
			Multiple samples must be passed as an ExcelFile object.

		temp: float
			Temperature at which to calculate degassing paths, in degrees C.

		system: str
			OPTIONAL. Default value is 'closed'. Specifies the type of calculation performed, either open system or closed
			system degassing. Possible inputs are 'open' and 'closed'.

		Returns
		-------
		?????

		"""

















