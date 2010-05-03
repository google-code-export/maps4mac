import subprocess
import pgdb as DBAPI
import pg as db_errors
_db_suffixes = ("_point", "_line","_polygon","_roads","_nodes","_ways","_rels")

def get_current_names(**kwargs):
    db_args = dict()
    db_args['host'] = kwargs.get('host','localhost')
    db_args['user'] = kwargs.get('user','postgres')
    db_args['password'] = kwargs.get('password','')
    db_args['database'] = kwargs.get('database','osm')
    
    extracts = list()
    
    con = DBAPI.connect(**db_args)
    try:
        cur = con.cursor()
        cur.execute("SELECT tablename FROM pg_tables WHERE schemaname='public'")
        tables = [t[0] for t in cur.fetchall()]
        for table in tables:
            if table.endswith("_point"):
                extracts.append(table[:-len("_point")])
    finally:
        con.close()
    return extracts

def loadExtract(osmFile,extractName,**kwargs):
    db_args = dict()
    db_args['host'] = kwargs.get('host','localhost')
    db_args['user'] = kwargs.get('user','postgres')
    db_args['password'] = kwargs.get('password','')
    db_args['database'] = kwargs.get('database','osm')
    
    if extractName in get_current_names(**db_args):
        raise Exception("Extract with that name already in DB")
    
    #FIXME: use host, password
    args = ["./osm2pgsql", "-s", "-d", db_args['database'], "-U", db_args['user'],"-S","default.style","--prefix",extractName,osmFile]
    
    output = subprocess.Popen(args, stdout=subprocess.PIPE).communicate()[0]
    #print output

def dropExtract(extractName,**kwargs):
    db_args = dict()
    db_args['host'] = kwargs.get('host','localhost')
    db_args['user'] = kwargs.get('user','postgres')
    db_args['password'] = kwargs.get('password','')
    db_args['database'] = kwargs.get('database','osm')
    
    con = DBAPI.connect(**db_args)
    cur = con.cursor()
    try:
        for suffix in _db_suffixes:
            tbl_name = extractName + suffix
            
            try:
                print tbl_name
                cur.execute("SELECT DropGeometryTable('%s')" % (tbl_name))
                print cur.fetchone()[0]
            except db_errors.ProgrammingError as e:
                print "Couldn't drop %s: %s" % (tbl_name, e)
        con.commit()
    finally:
        con.close()

def buildMapnikXML(extractName, **kwargs):
    mapnik_args = dict()
    mapnik_args['host'] = kwargs.get('host','localhost')
    mapnik_args['port'] = kwargs.get('port','5432')
    mapnik_args['user'] = kwargs.get('user','postgres')
    mapnik_args['password'] = kwargs.get('password','')
    mapnik_args['dbname'] = kwargs.get('database','osm')
    
    #FIXME: We can probably calculate this based on the extract
    mapnik_args['estimate_extent'] = 'true'
    mapnik_args['extent'] = ''
    
    mapnik_args['prefix'] = extractName
    mapnik_args['world_boundaries'] = kwargs.get('world_boundaries','./world_boundaries/')
    
    #FIXME: Can we determine the import projection from the DB?
    mapnik_args['epsg'] = kwargs.get('epsg','900913;')
    mapnik_args['symbols'] = kwargs.get('symbols','./symbols/')
    
    inc_files = ['inc/settings.xml.inc', 'inc/datasource-settings.xml.inc']
    for inc_file in inc_files:
        infile = open(inc_file + ".template")
        outfile = open(inc_file, "w")
        
        s = infile.read()
        s = s % mapnik_args
        outfile.truncate(0)
        outfile.write(s)
        
        infile.close()
        outfile.close()
        
    import mapnik
    m = mapnik.Map(1,1)
    mapnik.load_map(m,"osm_template.xml",True)
    mapnik.save_map(m,extractName + ".xml")

if __name__ == "__main__":
    import sys
    db_args = {'host':'localhost', 'user':'postgres', 'database':'osm_test'}
    
    print get_current_names(**db_args)
    
    db_name = sys.argv[1]
    file_name = "./%s.osm" % db_name

    loadExtract(file_name,db_name,**db_args)
    buildMapnikXML(db_name, **db_args)

    print get_current_names(**db_args)

    #dropExtract("arcata",**db_args)

    #print get_current_names(**db_args)
