import sublime, sublime_plugin
import os
import json
import re

class AssistantCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		
		fp = open("./Data/Packages/User/properties.json")
		
		aiml = json.load(fp)
		self.stopWords = ['a', 'an', 'the', 'with', 'and']
		#now read the line till beginning of this line and trim the characters
		cur_line = self.view.substr(self.view.line(self.view.sel()[0]))
		#print(cur_line)
		words = cur_line.split(" ")
		nextWordType = ""
		self.appName = ''
		self.functionName = ''
		self.dependencyName = []
		self.varArr = {}
		self.commaReqd = ""
		curContext = aiml


		for key, value in aiml.items():
			
			if(key == words[0]):
				#found command
				words.remove(words[0])
				curContext = aiml[key]
				for word in words:
					if word.strip() == '':
						continue
					word = self.cleanSpecialChars(word);
					ans, nextWordType = self.isStopWord(word, nextWordType, curContext)
					
					if ans:
						pass
					else:
						if nextWordType == "":
							#match next command
							matchInd = self.match(curContext, word)
							curContext = curContext[matchInd]
							
						else:
							if "extra" in nextWordType and nextWordType['extra'] == "pack":
								if nextWordType['preposition_type'] not in self.varArr:
									self.varArr[nextWordType['preposition_type']] = [];
								self.varArr[nextWordType['preposition_type']].append(word);

							else:
								self.varArr[nextWordType['preposition_type']] = word
				
				#write down the command for the case
				output = self.processOutput(curContext["output"])
				self.view.replace(edit, self.view.line(self.view.sel()[0]), output)
				#self.view.insert(edit, (self.view.line(self.view.sel()[0])).a, output)
				break
		
	def processOutput(self, input):
		output = re.sub("\{\{[a-zA-Z0-9\|]*\}\}", lambda x:x.group(0).replace(x.group(0), self.replaceVar(x.group(0))), input)
		return output

	def replaceVar(self, x):
		
		x = x.replace("{", "");
		x = x.replace("}", "");
		print(x)
		retVar = "";
		if "|" in x:
			#filters applied
			commandList = x.split("|")
			varName = commandList[0]
			commandList.remove(varName)
			if varName not in self.varArr:
				return "''";
			retVar = self.varArr[varName]
			for comm in commandList: 
				if comm == "standardize": 
					retVar = self.standardize(retVar);	
				if comm == "stringify":
					if(isinstance(retVar, list)):

						retVar = (", ".join("'{0}'".format(w) for w in retVar))
					else:
						retVar = "'" + retVar + "'"
					#stringify should be last command
			if(isinstance(retVar, list)):
				retVar = (", ".join(retVar));
		else:
			varName = x
			if varName not in self.varArr:
				return "''";
			if(isinstance(self.varArr[varName], list)):
					retVar = (", ".join(self.varArr[varName]))
			else:
					retVar = self.varArr[varName]
		
		return retVar;

	def match(self, context, word):
		i = 0
		for obj in context:
			matchArray = obj['matches'].split("|")
			for matchWord in matchArray:
				if matchWord == word:
					return i
			i += 1
			


	def isStopWord(self, word, nextWordType, curContext):

		if word in self.stopWords:
			if(nextWordType != ""):
				return True, nextWordType
			else:
				return True, ""
		if isinstance(curContext, list):
			#not sure what to create right now
			return False, nextWordType
		prepositions = curContext['prepositions']
		for opt in prepositions:
			if word in opt['preps'].split('|'):
				return True, opt;
		
		
		#its not a stop word just maintain previous wordtype condition
		return False, nextWordType

	def standardize(self, word):
		standardInjections = {
			"http": "$http",
			"scope": "$scope",
			"timeout": "$timeout"
		}
		if isinstance(word, list):
			for i in range(len(word)):
				if word[i] in standardInjections:
					word[i] = standardInjections[word[i]]
		else: 
			#string instance replace keys with values
			for key in standardInjections: 
				word = word.replace(key, standardInjections[key]);
		
		return word

	def cleanSpecialChars(self, word):
		word = word.replace(",", "");
		word = word.replace(";", "");

		return word;
