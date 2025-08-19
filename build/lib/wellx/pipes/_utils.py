import pandas as pd

class utils:
	
	@staticmethod
	def heads(frame,*args,include:tuple[str]=None,exclude:tuple[str]=None)->list[str]:
		"""
		Returns the list of arguments that are in the DataFrame and after
		including & excluding the dtypes.

		Parameters:

		*args	: Positional column names to check in the DataFrame.

		include  : Include dtypes for the head selection.
		exclude  : Exclude dtypes for the head selection.

		Return:

		A list of column names that exist in the DataFrame and that match the
		specified include and exclude criteria.

		"""
		head_list = [head for head in args if head in frame.columns]

		if include is None and exclude is None:
			return head_list

		head_list += frame.select_dtypes(include=include,exclude=exclude).columns.tolist()

		return list(set(head_list))

	@staticmethod
	def join(frame,*args,separator=None,**kwargs)->pd.DataFrame:
		"""
		Joins the frame columns specified by the args and kwargs and
		returns a new joined frame.

		Parameters:

		*args	  : Positional column names to check in the DataFrame.
		separator : The characters to add between column items.
		**kwargs  : include and exclude dtypes for the head selection.

		Returns:

		The joined frame.

		"""
		heads = utils.heads(frame,*args,**kwargs)

		separator = " " if separator is None else separator

		value = frame[heads].astype("str").agg(separator.join,axis=1)

		return pd.DataFrame({separator.join(heads):value})

	@staticmethod
	def filter(frame,column:str,*args)->pd.DataFrame:
		"""
		Filters the non-empty input frame by checking the 
		series specified by column for args.
		
		Parameters:
		----------
		column   : Column name where to search for args
		*args	: Positional values to keep in the column series.

		Returns:
		-------
		A new filtered frame.
		
		"""
		return frame[frame[column].isin(args)].reset_index(drop=True)

	@staticmethod
	def groupsum(frame,column:str,*args):
		"""
		Groups the non-empty input frame based on column and
		returns a new frame after summing the other columns.
		
		Parameters:
		----------
		column   : Column name which to group
		*args	: Positional values to keep in the column series.

		Returns:
		-------
		A new summed frame.

		"""
		frame = frame[utils.heads(frame,column,include=('number',))]

		frame = utils.filter(frame,column,*args)

		frame[column] = "".join(frame[column].unique())

		frame = frame.groupby(column).sum().reset_index(drop=True)

		return frame

if __name__ == "__main__":

	import pandas as pd

	frame = {
		"name" : ["john","smith","python","john","georgina"],
		"age"  : [32,47,23,25,23],
		"rate" : [1.,5.,6.,8.5,9],
		}

	frame = pd.DataFrame(frame)

	utils = utils()

	print(frame)

	print(utils.heads(frame,'name','age',exclude='number'))

	print(utils.join(frame,'name','age',separator="#"))

	print(utils.filter(frame,"name","john","georgina"))

	print(utils.groupsum(frame,"name","john","georgina"))

	print(frame)

	df = pd.DataFrame({
		"name": ["A", "B", "C", "A"],
		"city": ["X", "Y", "X", "Z"],
		"age":  [10, 20, 30, 40],			  # int
		"score": [1.5, 2.0, 3.5, 4.0],		 # float
		"is_ok": [True, False, True, True],	# bool
		"date": pd.to_datetime(["2024-01-01","2024-01-02","2024-01-03","2024-01-04"])
	})

	print(utils.heads(df,include=('number',)))

	print(utils.groupsum(df, "name", "A", "B"))

	print(df)