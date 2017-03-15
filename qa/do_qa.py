"""do_qa.py

Purpose: wrapper script for qa module.
"""
from qa import qa_data

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()

    req_named = parser.add_argument_group('Required named arguments')

    req_named.add_argument('-m', action='store', dest='dir_mast', type=str,
                           help='Master directory', required=True)

    req_named.add_argument('-t', action='store', dest='dir_test', type=str,
                           help='Test directory', required=True)

    req_named.add_argument('-o', action='store', dest='dir_out', type=str,
                           help='Output directory', required=True)

    parser.add_argument('-x', action='store_true', dest='xml_schema',
                        help='Path to XML schema', required=False)

    parser.add_argument('--no-archive', action='store_false', dest='archive',
                        help='Look for individual files, instead of g-zipped'
                             ' archives.', required=False)



    parser.add_argument('--verbose', action='store_true', dest='verbose',
                        help='Enable verbose logging.', required=False)

    arguments = parser.parse_args()

    qa_data(**vars(arguments))
