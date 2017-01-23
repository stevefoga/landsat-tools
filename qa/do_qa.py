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

    parser.add_argument('-verbose', action='store', dest='verbose', type=bool,
                        help='Verbose logging.', default=False, required=False)

    arguments = parser.parse_args()

    print(arguments)
  
    qa_data(**vars(arguments))
