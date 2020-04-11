from collections import namedtuple

class MetadataElement(object):
	def __init__(self, metadata=None):
		if metadata:
			self.metadata = metadata
		else:
			self.metadata = {}

	def add(self, key, val=None):
		if isinstance(key,dict):
			# if key is a dictionary, add each element individually
			for dkey in key:
				self.add(dkey,key[dkey])
		else:
			# if key is not a dictionary (ie, just an item) val should be a list of strings
			if key in self.metadata:
				for item in val:
					if not item in self.metadata[key]:
						self.metadata[key].append(item)
			else:
				self.metadata[key]=val

	def remove(self, key, val=None):
		if val is None:
			self.metadata.pop(key)
		else:
			if val in self.metadata[key]:
				self.metadata[key].remove(val)
			if self.metadata[key] == []:
				self.metadata.pop(key)
	def render(self, preceding_space=True):
		output = " " if preceding_space else ""
		for key in self.metadata:
			if self.metadata[key]:
				output += f'{key}="'
				output += " ".join(self.metadata[key])
				output += '" '
		return output
	def __repr__(self):
		return "Metadata(" + str(self.metadata, preceding_space=False) + ")"

	def __str__(self):
		return self.render()

	def __add__(self, other):
		output = MetadataElement()
		for key in self.metadata:
			output.add(key, self.metadata[key])
		for key in other.metadata:
			output.add(key, other.metadata[key])
		return output

# list1, list2 = (list(t) for t in zip(*sorted(zip(list1, list2))))

class Metadata(object):
	def __init__(self, *, rows, columns, has_header_row, has_header_column):
		if has_header_row:
			self.whole_header_row = MetadataElement()
			self.header_row_elements = [MetadataElement()] * columns
			self.has_header_row = True
		if has_header_column:
			self.whole_header_col = MetadataElement()
			self.header_col_elements = [MetadataElement()] * rows
			self.has_header_col = True
		self.whole_table = MetadataElement()
		self.whole_row = [MetadataElement()] * rows
		self.whole_col = [MetadataElement()] * columns
		self.data = [[MetadataElement() for i in range(columns)] for j in range(rows)]

class Table(object):
	def __init__(self, *, has_header_row=True, has_header_column=True):
		self.has_header_column = has_header_column
		self.has_header_row = has_header_row
		self.data = None
		#self.has_metadata=False

	def initialise(self, *, rows, columns, default=""): #, has_metadata=False ):
		if self.data is None:
			self.data = [[default for i in range(columns)] for j in range(rows)]
			self.rows=rows
			self.columns=columns
			self.metadata = Metadata(rows=self.rows, 
									 columns= self.columns,
									 has_header_row = self.has_header_row,
									 has_header_column = self.has_header_column)

	def set_column_headers(self, column_headers): #, metadata=None):
		if self.has_header_column:
			if self.columns == len(column_headers):
				self.column_headers = column_headers
			else:
				print("Length mismatch")
	def set_row_headers(self, row_headers): #, metadata=None):
		if self.has_header_row:
			if self.rows == len(row_headers):
				self.row_headers = row_headers
			else:
				print("Length mismatch")

	def initialise_by_headers(self, *, row_headers, column_headers, default=""): #, has_metadata=False):
		self.initialise(rows=len(row_headers), columns=len(column_headers), default=default) #, has_metadata=has_metadata)
		self.set_row_headers(row_headers)
		self.set_column_headers(column_headers)

	def add_table_metadata(self, *, metadata):
		self.metadata.whole_table.add(metadata)

	def add_row_metadata(self, *, metadata, row_index=None, row_header=None):
		if row_index is None:
			row_index = self.row_headers.index(row_header)
		self.metadata.whole_row[row_index].add(metadata)

	def add_col_metadata(self, *, metadata, col_index=None, col_header=None):
		if col_index is None:
			col_index = self.column_headers.index(col_header)
		self.metadata.whole_col[col_index].add(metadata)

	def add_header_row_metadata(self, *, metadata):
		self.metadata.whole_header_row.add(metadata)

	def add_header_col_metadata(self, *, metadata=""):
		self.metadata.whole_header_col.add(metadata)

	def insert_into(self, *, value="", metadata=None, col_index=None, col_header=None, row_index=None, row_header=None):
		if (col_index is None and col_header is None) or \
		   (row_index is None and row_header is None):
		   return
		if col_index is None:
			col_index = self.column_headers.index(col_header)
		# else:
			# col_index += 1
		if row_index is None:
			row_index = self.row_headers.index(row_header)
		# else:
			# row_index += 1
		if value:
			self.data[row_index][col_index] = value
			#print(f"inserted {value} to {row_index},{col_index}")
		if metadata:
			self.metadata.data[row_index][col_index].add(metadata)

	def build_raw_output_table(self):

		output = [["" for i in range(self.columns+1)] for j in range(self.rows + 1)]

		start_row = -1 if self.has_header_row else 0
		start_column = -1 if self.has_header_column else 0
		for row_index in range(start_row, self.rows):
			for col_index in range(start_column, self.columns):
				if row_index < 0 and col_index < 0:
					val = ""
				elif row_index < 0:
					val = self.column_headers[col_index]
				elif col_index < 0:
					val = self.row_headers[row_index]
				else:
					val = self.data[row_index][col_index]
				output[row_index+1][col_index+1] = val

		return output

	def build_html_table(self):

		#output = [["" for i in range(self.columns+1)] for j in range(self.rows + 1)]
		output = f"<table{self.metadata.whole_table}>"

		start_row = -1 if self.has_header_row else 0
		start_column = -1 if self.has_header_column else 0

		for row_index in range(start_row, self.rows):
			for col_index in range(start_column, self.columns):
				# if col_index == start_column:
				# 	if row_index == start_row
				# 	val += ""
				val = ""
				if row_index < 0 and col_index < 0:
					# We are in the uppermost right cell
					val += f"\n\t<thead>\n\t\t<tr{self.metadata.whole_header_row}>\n\t\t\t<th></th>"
				elif row_index == 0 and col_index == start_column:
					# We're in the top-right cell of the body
					val += "\n\t<tbody>"
				elif col_index == start_column:
					# The remainder of the header column
					# Apply whole-row metadata
					val += f"\n\t\t<tr{self.metadata.whole_row[row_index]}>"

				if row_index < 0 and col_index < 0:
					# The top-rightmost row that is empty
					pass
				elif row_index < 0:
					# If we're on the top row
					val += f"\n\t\t\t<th"
					# Apply whole-column metadata and header-row metadata
					val += f"{self.metadata.whole_col[col_index]+self.metadata.header_row_elements[col_index]}>"
					val += f"{self.column_headers[col_index]}</th>"
				elif col_index < 0:
					# We're in the first column
					val += f"\n\t\t\t<th"
					val += f"{self.metadata.whole_header_col+self.metadata.header_col_elements[row_index]}" 
					val += f">{self.row_headers[row_index]}</th>"
				else:
					val += "\n\t\t\t<td"
					val += f"{self.metadata.data[row_index][col_index]}"
					if self.data[row_index][col_index]:
						val += f"><div class=\"drag\">{self.data[row_index][col_index]}</div></td>"
					else:
						val += "></td>"

				if col_index == self.columns - 1:
					val += "\n\t\t</tr>"
					if row_index == -1:
						val += "\n\t</thead>"
					elif row_index == self.rows - 1:
						val += "\n\t</tbody>\n</table>"

				output += val
		return output	

	# def elements(self):
	# 	output = []
	# 	Value = namedtuple("Value", ['row','col','data','metadata'])
	# 	for row in range(self.rows):
	# 		for col in range(self.columns):



if __name__ == "__main__":
	G = Table()
	G.initialise_by_headers(row_headers=[1,2,3], column_headers=[4,5,6], metadata=True, default="0")
	G.insert_into(value=22,col_header=4,row_header=2,metadata='style="background-color:red"')
	G.add_row_metadata(row_header=3, metadata='style="background-color:red"')
	G.add_first_col_metadata(metadata='style="background-color:red"')
	# G.render_html()
	with open("output.html", "w") as f:
		f.write(G.build_html_table())
	print("Done")