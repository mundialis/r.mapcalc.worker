#!/usr/bin/env python3
#
############################################################################
#
# MODULE:       r.mapcalc.worker
# AUTHOR(S):    Guido Riembauer
# PURPOSE:      This is a worker addon to run r.mapcalc in different mapsets
# COPYRIGHT:    (C) 2020-2022 by mundialis GmbH & Co. KG and the GRASS
#               Development Team
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
############################################################################

# %module
# % description: Runs r.mapcalc as a worker in different mapsets.
# % keyword: raster
# % keyword: import
# % keyword: projection
# % keyword: parallel
# %end

# %option
# % key: region
# % type: string
# % required: yes
# % multiple: no
# % description: Saved region to use r.mapcalc on. Add @<source_mapset> to the region if it lies outside the current mapset
# %end

# %option
# % key: newmapset
# % type: string
# % required: yes
# % multiple: no
# % description: Name of new mapset to run r.mapcalc in
# %end

# %option
# % key: expression
# % type: string
# % required: yes
# % multiple: no
# % description: Mapcalc expression to be calculated. Add @<source_mapset> to the individual maps used in the expression
# %end


import os
import shutil
import sys
import grass.script as grass


def main():

    # set some common environmental variables, like:
    os.environ.update(
        dict(
            GRASS_COMPRESS_NULLS="1",
            GRASS_COMPRESSOR="LZ4",
            GRASS_MESSAGE_FORMAT="plain",
        )
    )

    # actual mapset, location, ...
    env = grass.gisenv()
    gisdbase = env["GISDBASE"]
    location = env["LOCATION_NAME"]

    new_mapset = options["newmapset"]
    grass.message(_("New mapset: <%s>" % new_mapset))
    grass.utils.try_rmdir(os.path.join(gisdbase, location, new_mapset))

    # create a private GISRC file for each job
    gisrc = os.environ["GISRC"]
    newgisrc = "%s_%s" % (gisrc, str(os.getpid()))
    grass.try_remove(newgisrc)
    shutil.copyfile(gisrc, newgisrc)
    os.environ["GISRC"] = newgisrc

    # change mapset
    grass.message(_("GISRC: <%s>" % os.environ["GISRC"]))
    grass.run_command("g.mapset", flags="c", mapset=new_mapset)

    # set region
    grass.run_command("g.region", region=options["region"], quiet=True)

    # run mapcalc
    grass.message(_("Running r.mapcalc ..."))

    grass.run_command("r.mapcalc", expression=options["expression"], quiet=True)

    output = options["expression"].split("=")[0].strip()
    if not grass.find_file(name=output, element="raster", mapset=options["newmapset"])[
        "file"
    ]:
        grass.fatal(_("ERROR calculating %s" % output))

    grass.utils.try_remove(newgisrc)
    os.environ["GISRC"] = gisrc


if __name__ == "__main__":
    options, flags = grass.parser()
    sys.exit(main())
