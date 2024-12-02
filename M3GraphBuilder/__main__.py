from M3GraphBuilder.utils import load_config_from_ini_file, setup_logging
from M3GraphBuilder.cli import setup_parser

M3GB_config = {}

def main():
    parser = setup_parser()
    args = parser.parse_args()
    args.func(args, M3GB_config)


if __name__ == "__main__":
    M3GB_config = load_config_from_ini_file()
    setup_logging(M3GB_config, "M3GB.txt")
    main()
