class SearchStringParseException(Exception):
    pass

class SearchParser():
    def __init__(self, tags):
        self.knownCommands = [
            "sql",
            "and",
            "or",
            "=",
            "is",
            "contains",
            "within",
            "in",
            "view",
        ]
        
        self.knownTags = tags

    def tokenize(self, s):
        if not s:
            return None
        quote = None
        tokens = [""]
        for c in s:
            if quote and c == quote:
                quote = None
            elif quote:
                tokens[-1] += c
            elif not quote and c != " ":
                if c == "\"":
                    quote = c
                elif c == "'":
                    quote = c
                elif c == "(":
                    if tokens[-1]:
                        tokens.append("(")
                    else:
                        tokens[-1] = "("
                    tokens.append("")
                elif c == ")":
                    if tokens[-1]:
                        tokens.append(")")
                    else:
                        tokens[-1] = ")"
                    tokens.append("")
                elif c == "=":
                    # Special handling so equals can touch the last token
                    if tokens[-1]:
                        tokens.append("=")
                    else:
                        tokens[-1] = "="
                    tokens.append("")
                else:
                    tokens[-1] += c
            else:
                tokens.append("")
        
        return [x for x in tokens if x != '']
        #return tokens

    def parseWithinUnits(self, tokens):
        try:
            if tokens[0].lower() != "within":
                return None
            
            distance = float(tokens[1])
            units = tokens[2].lower()
            if units == "km" or units == "kilometers":
                distance = distance * 1000
            elif units == "mi" or units == "miles":
                distance = distance * 1609.344
            elif units == "ft" or units == "feet":
                distance = distance * 0.3048
            elif units == "m" or units == "meters":
                pass
            else:
                return None
            return (3, "withinUnits", distance)
        except:
            return None

    def parseWithinView(self, tokens):
        try:
            if (tokens[0].lower() == "within" or tokens[0].lower() == "in") and tokens[1].lower() == "view":
                return (2, "withinView")
            return None
        except:
            return None

    def parseTagEquals(self, tokens):
        try:
            tags = self.knownTags
            
            if tokens[0] not in tags:
                return None
            tag = tokens[0]
            
            if not (tokens[1].lower() == "is" or tokens[1] == "="):
                return None
            value = tokens[2]
            
            return (3, "tagEquals", (tag, value))
        except:
            return None

    def parseTagContains(self, tokens):
        try:
            tags = self.knownTags
            
            if tokens[0] not in tags:
                return None
            tag = tokens[0]
            
            if not tokens[1].lower() == "contains":
                return None
            value = tokens[2]
            
            return (3, "tagContains", (tag, value))
        except:
            return None

    def parseNotNull(self, tokens):
        try:
            tags = self.knownTags
            
            if tokens[0] not in tags:
                return None
            tag = tokens[0]
            
            if not (tokens[1].lower() == "is" and tokens[2].lower() == "not" and tokens[3].lower() == "null"):
                return None
            
            return (4, "tagNotNull", tag)
        except:
            return None


    def tokenparse(self, raw_tokens, recursed = False):
        rules = [
            #parseWithinUnits,
            self.parseWithinView,
            self.parseNotNull,
            self.parseTagEquals,
            self.parseTagContains,
        ]
        
        tokens = raw_tokens[:]
        parsed = []
        
        while tokens:
            rule_result = None
            if tokens[0] == "(":
                tokens = tokens[1:]
                result = self.tokenparse(tokens, recursed=True)
                if not result:
                    return None
                tokens = tokens[result[0]:]
                parsed.append(result[1])
            elif tokens[0] == ")":
                if not recursed:
                    print "Unmatched )"
                    return None
                return (len(raw_tokens) - len(tokens) + 1, parsed)
            else:
                for rule in rules:
                    rule_result = rule(tokens)
                    if rule_result is not None:
                        tokens = tokens[rule_result[0]:]
                        parsed.append(rule_result[1:])
                        break
                
                if not rule_result:
                    raise SearchStringParseException("Couldn't parse end of string: ", tokens)
            
            if tokens:
                if tokens[0].lower() == "or":
                    parsed.append("or")
                    tokens = tokens[1:]
                elif tokens[0].lower() == "and":
                    parsed.append("and")
                    tokens = tokens[1:]
                elif tokens[0] != ")":
                    # If there's nothing between rules assume and
                    parsed.append("and")
        
        if recursed:
            print "Unmatched ("
            return None
            
        if not parsed:
            return None
        
        return parsed

    def parse(self, search_string):
        if search_string[:4] == "sql ":
            print "No Parse"
            return search_string[4:]
        else:
            tokens = self.tokenize(search_string)
            
            def containsCommands(tokens):
                for command in self.knownCommands:
                    if command in tokens:
                        return True
            
            doParse = containsCommands(tokens)
            
            # Check if it's a simple in view query
            try:
                inView = self.parseWithinView(tokens[-2:])
                if inView and not containsCommands(tokens[:-2]):
                    return [("tagContains", ("name", " ".join(tokens[:-2]))), "and", inView[1:]] 
            except:
                pass
            
            if doParse:
                print "Complex"
                return self.tokenparse(tokens)
            else:
                print "Simple"
                return [("tagContains", ("name", " ".join(tokens)))]
        return tokens

def parsedToPGSQL(parsed):
    sqlString = ""
    for rule in parsed:
        if type(rule) == list:
            sqlString += "(" + parsedToPGSQL(rule) + ") "
        elif rule[0] == "tagEquals":
            sqlString += "\"%s\" = '%s' " % rule[1]
        elif rule[0] == "tagContains":
            sqlString += "(to_tsvector('simple',\"%s\") @@ to_tsquery('simple','%s')) " % rule[1]
        elif rule[0] == "tagNotNull":
            sqlString += "\"%s\" is not null " % rule[1]
        elif rule == "or":
            sqlString += "or "
        elif rule == "and":
            sqlString += "and "
        else:
            raise SearchStringParseException("Rule type not supported by PGSQL", rule)
    
    return sqlString

def parsedToSQLite(parsed):
    sqlString = ""
    for rule in parsed:
        if type(rule) == list:
            sqlString += "(" + parsedToSQLite(rule) + ") "
        elif rule[0] == "tagEquals":
            sqlString += "\"%s\" = '%s' " % rule[1]
        elif rule[0] == "tagContains":
            sqlString += "\"%s\" like '%%%s%%') " % rule[1]
        elif rule[0] == "tagNotNull":
            sqlString += "\"%s\" is not null " % rule[1]
        elif rule == "or":
            sqlString += "or "
        elif rule == "and":
            sqlString += "and "
        else:
            raise SearchStringParseException("Rule type not supported by PGSQL", rule)
    
    return sqlString

def main(exampleStrings):
    tags = [
        "name",
        "shop",
        "place",
        "boundary",
        "amenity",
    ]
    
    parser = SearchParser(tags)
    
    for example in exampleStrings:
        try:
            result = parser.parse(example)
            print result
            if result and type(result) == list:
                print parsedToPGSQL(result)
                print parsedToSQLite(result)
            elif type(result) == str:
                print result
        except SearchStringParseException as e:
            print e

if __name__ == "__main__":
    exampleStrings = [
        "sql boundary='national park' and name like '%National Forest'",
        "boundary = national_park",
        "shop = book",
        "shop is book",
        "shop near book",
        "name = 'Barnes and Noble'",
        "shop = book and name = 'Barnes and Noble'",
        "shop = book and name = \"Barnes and Noble\" in view",
        "shop = book AND name = 'Barnes and Noble' within 50 miles",
        "monkies = 50",
        "shop = book and name contains Barnes",
        "amenity = cafe or amenity = fast_food",
        "shop = book and (name contains Barnes or name contains Borders)",
        "shop = book (name contains Barnes or name contains Borders) in view",
        "name = Portland AND place is not null",
        "name = 'Bad Bracket 1' or (",
        "name = 'Bad Bracket 2' or amenity is not null )",
        "Jamaba Juice in view",
    ]
    main(exampleStrings)