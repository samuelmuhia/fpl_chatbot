"""
Main Application Module
Runs the FPL chatbot interface.
"""
from fpl_client import FPLClient
from chatbot import gpt_fallback, print_help

def main():
    """Main entry point for the FPL assistant."""
    print("🤖 FPL Management Chatbot (Type 'help' for commands, 'quit' to exit)")
    print("-" * 70)

    fpl = FPLClient()

    while True:
        text = input("\n> ").strip()
        if not text:
            continue

        cmd = text.split()[0].lower()
        args = text[len(cmd):].strip()

        if cmd in ["quit", "exit", "q"]:
            print("Goodbye and best of luck this gameweek!")
            break

        if cmd == "help":
            print_help()
            continue

        if cmd == "compare":
            names = [n.strip() for n in args.split(",") if n.strip()]
            if len(names) < 2:
                print("Usage: compare <name1>,<name2>")
                continue

            table = fpl.compare_players(names[:2])
            for row in table:
                if "error" in row:
                    print(row["error"])
                    continue
                print(f"\n{row['name']} ({row['team']})")
                print(f"  Total points: {row['points']}, PPG: {row['points_per_game']}, form: {row['form']}")
                print(f"  Recent points: {row['recent_points']}, recent form: {row['recent_form']}")
            continue

        if cmd == "injuries":
            if not args:
                print("Usage: injuries <player name>")
                continue
            print(fpl.injury_report(args))
            continue

        if cmd == "form":
            if not args:
                print("Usage: form <player name>")
                continue
            print(fpl.form_report(args))
            continue

        if cmd == "suggest":
            top_n = 5
            if args.isdigit():
                top_n = int(args)
            print("Top suggestions by current FPL form:")
            print(fpl.team_suggestions(top_n))
            continue

        if cmd == "chat":
            query = args.strip()
            if not query:
                print("Usage: chat <question text>")
                continue
            print(gpt_fallback(query))
            continue

        # fallback general question
        print(gpt_fallback(text))

if __name__ == "__main__":
    main()