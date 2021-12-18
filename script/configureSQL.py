# 16.17.12. Loading RDF | Openlink Virtuoso Documentation
# cf. http://docs.openlinksw.com/virtuoso/rdfperfloading/

import re
import argparse
from pathlib import Path

# argument parser settings ----------------------------------------------------
parser = argparse.ArgumentParser()
parser.add_argument("extension", type=str, help="set extension of your data")
parser.add_argument("--target-graph", "-tg", type=str, help="set your named graph")
parser.add_argument(
    "--origin",
    type=str,
    help="if not set target graph, set your origin or protocol+fqdn",
)
parser.add_argument(
    "--protocol",
    type=str,
    help="if not set target graph, set your origin or protocol+fqdn",
)
parser.add_argument(
    "--fqdn",
    type=str,
    help="if not set target graph, set your origin or protocol+fqdn",
)
parser.add_argument(
    "--mount-folder",
    "-mf",
    type=str,
    help="path to folder mounted on virtuoso container",
)
# -----------------------------------------------------------------------------
# define consts ---------------------------------------------------------------
ARGS = parser.parse_args()

EXT = re.sub("^\W+", "", ARGS.extension)
PROTOCOL = "http" if not ARGS.protocol else ARGS.protocol
FQDN = "graph.example.com" if not ARGS.fqdn else ARGS.fqdn
MOUNT_FOLDER = "/mount/data" if "mount-folder" not in ARGS else ARGS["mount-folder"]
IsGraphSpecified = False if "target-graph" not in ARGS else ARGS["target-graph"]
LOADING_FUNCTION = "TTLP_MT" if EXT == "ttl" else "RDF_LOAD_RDFXML"


def makeGraph(dir, name):
    if not ARGS.origin:
        return f"{PROTOCOL}://{FQDN}/{dir}/{name}#"
    else:
        origin = ARGS.origin
        return f"{origin}/{dir}/{name}#"


# -----------------------------------------------------------------------------
# main ------------------------------------------------------------------------
CWD = Path.cwd()
DIR_DATA = CWD / "data"
TTL_LOADER = CWD / "script" / "initialLoader.sql"

# 行末のセミコロンを忘れずに！
content = """
create procedure DB.DBA.MSG_OUTOUT (in x varchar)
{
  declare str_out any;
  declare str varchar;

-- Pass correct result metadata to client
  result_names (str);

-- Get a new string output stream
  str_out := string_output();

  http (x, str_out);
  result (str_out);
};

log_enable(2,1);\n
"""

total = len(list(DIR_DATA.glob(f"**/*.{EXT}")))
count = 0

for filepath in DIR_DATA.glob(f"**/*.{EXT}"):
    parts = list(filepath.parts)
    idx = parts.index("turtle")
    relativeParent = "/".join(parts[idx:-1])
    graph = (
        ARGS["target-graph"]
        if IsGraphSpecified
        else makeGraph(relativeParent, filepath.stem)
    )

    # bulk load ではなく，ファイル一つずつ読み込むパターン：DB.DBA.TTLP_MT && checkpoint;
    # TTLのロード(DB.DBA.TTLP_MT) | SPARQLthon19/TripleLoad | TogoWiki
    # cf. https://wiki.lifesciencedb.jp/mw/SPARQLthon19/TripleLoad#TTL.E3.81.AE.E3.83.AD.E3.83.BC.E3.83.89.28DB.DBA.TTLP_MT.29
    sql = (
        f"DB.DBA.{LOADING_FUNCTION} (file_to_string_output('{MOUNT_FOLDER}/{relativeParent}/{filepath.name}'), "
        + "'', "
        + f"'{graph}', "
        + "81 ) ;"
    )
    content += f"{sql}\ncheckpoint;\n\n"

    # count up
    count += 1
    print("\r[{}]".format("#" * 50 * (count // total)), end="")

# 'initialLoader.sql' にファイルごとに必要なSQL文を書き込む
with TTL_LOADER.open(encoding="utf-8", mode="w") as f:
    f.write(content)
    f.write("MSG_OUTOUT ( '######### initialLoader.sql completed ! '#########' );\n")
