from __future__ import annotations

from pathlib import Path

from gym.gym import ValidationError, NotFoundError, Gym
from gym.storage import load_gym, save_gym

from gym.people import Member, Trainer
from gym.memberships import BasicMembership, PremiumMembership
from gym.pricing import NoDiscount, PercentOff, FixedPrice
from gym.workouts import Exercise

SAVE_PATH = Path("data/gym.json")

def prompt(text: str) -> str:
    return input(text).strip()

def prompt_float(text: str) -> float:
    raw = prompt(text)
    try:
        return float(raw)
    except (ValueError, TypeError):
        raise ValidationError ("Please enter a valid number.")
    
def prompt_int(text: str) -> int:
    raw = prompt(text)
    try:
        return int(raw)
    except (ValueError, TypeError):
        raise ValidationError ("Please enter a valid integer.")
    
def choose_membership() -> object:
    print("\n Choose membership: ")
    print("1) Basic")
    print("2) Premium")
    choice = prompt("> ")

    print("\n Choose price policy: ")
    print("1) No discount")
    print("2) Percent off")
    print("3) Fixed Price")
    pchoice = prompt("> ")

    if pchoice == "1":
        policy = NoDiscount()

    elif pchoice == "2":
        discount = prompt_float("Discount (e.g. 0.20 for 20%): ")
        policy = PercentOff(discount=discount)

    elif pchoice == "3":
        price = prompt_float("Fixed monthly price: ")
        policy = FixedPrice(price=price)

    else:
        raise ValidationError ("Invalid price policy choice.")
    
    if choice == "1":
        return BasicMembership(price_policy=policy)
    
    elif choice == "2":
        return PremiumMembership(price_policy=policy)
    
    raise ValidationError ("Invalid membership type.")

def load_or_create_gym() -> Gym:
    if SAVE_PATH.exists():
        return load_gym(SAVE_PATH)
    name = prompt("Gym name: ")
    gym = Gym(name=name)
    SAVE_PATH.parent.mkdir(parents=True, exist_ok=True)
    save_gym(gym=gym, filepath=SAVE_PATH)
    return gym

def menu() -> None:
    gym = load_or_create_gym()

    while True:
        print("\n=================================")
        print(gym.summary() if hasattr(gym, "summary") else f"Gym: {gym.name}")
        print("===================================")
        print("1) Add member")
        print("2) List members")
        print("3) Charge member")
        print("4) Add trainer")
        print("5) List Trainers")
        print("6) Create Workout plan for member")
        print("7) Add exercise to plan")
        print("8) List plans for member")
        print("9) Save")
        print("0) Exit")
        choice = prompt("> ")

        try:
            if choice == "1":
                full_name = prompt("Member full name: ")
                email = prompt("Member email: ")
                membership = choose_membership()
                member = Member(full_name=full_name, email=email, membership=membership)
                gym.add_member(member=member)
                save_gym(gym=gym, filepath=SAVE_PATH)
                print(f"Member added: {member.full_name} ({member.id})")

            elif choice == "2":
                members = gym.list_members()
                if not members:
                    print("No members yet.")
                else:
                    for m in members:
                        print(f"-{m.full_name} | {m.email} | {m.membership_name} | {m.membership_status.value}")

            elif choice == "3":
                member_id = prompt("Member id: ")
                raw = prompt("Amount (blank = monthly price): ")
                try:
                    amount = None if raw.strip() == "" else float(raw)
                except (ValueError):
                    raise ValidationError ("Please enter a valid number.")
                record = gym.charge_member(member_id=member_id, amount=amount)
                save_gym(gym, SAVE_PATH)
                print(f"{record.status.value.upper()}: {record.message} (${record.amount:.2f})")

            elif choice == "4":
                full_name = prompt("Trainer Full name: ")
                email = prompt("Trainer Email: ")
                spec = prompt("Speciality (Optional): ")
                speciality = spec if spec else None
                trainer = Trainer(full_name=full_name, email=email, specialty=speciality)
                gym.add_trainer(trainer=trainer)
                save_gym(gym, SAVE_PATH)
                print(f"Added trainer: {trainer.full_name}, ({trainer.id})")

            elif choice == "5":
                trainers = gym.list_trainers()
                if not trainers:
                    print("No trainers yet.")
                else:
                    for t in trainers:
                        spec = getattr(t, "speciality", None)
                        print(f"-{t.full_name} | {t.email} | {spec or '-'}")

            elif choice == "6":
                member_id = prompt("Member_id: ")
                title = prompt("Plan title: ")
                plan = gym.create_workout_plan(member_id=member_id, title=title)
                save_gym(gym, SAVE_PATH)
                print(f"-Plan Created: ({plan.id}) | {plan.title}")

            elif choice == "7":
                plan_id = prompt("Plan id: ")
                name = prompt("Exercise name: ")
                sets = prompt_int("Sets: ")
                reps = prompt_int("Reps: ")
                load = prompt("Load (Optional): ")
                try:
                    load_val = None if load.strip() == "" else float(load)
                except ValueError:
                    raise ValidationError ("Load must be a valid number.")
                notes = prompt("Notes (Optional): ")
                notes_val = None if notes == "" else notes
                ex = Exercise(name=name, sets=sets, reps=reps, load=load_val, notes=notes_val)
                gym.add_exercise_to_plan(plan_id=plan_id, exercise=ex)
                save_gym(gym, SAVE_PATH)
                print(f"Exercise added: {ex.name} | {ex.sets} Sets | {ex.reps} reps")

            elif choice == "8":
                member_id = prompt("Member id: ")
                plans = gym.list_plans_for_member(member_id=member_id)
                if not plans:
                    print("No plans for this member.")
                else:
                    for p in plans:
                        print(f"\n Plan: {p.title} | ({p.id})")
                        for num, e in p.list_exercises_numbered():
                            load_txt = f"{e.load}" if e.load is not None else "-"
                            print(f"{num}. {e.name} | {e.sets}x{e.reps} | load: {load_txt}")

            elif choice == "9":
                save_gym(gym, SAVE_PATH)
                print("Saved")

            elif choice == "0":
                save_gym(gym, SAVE_PATH)
                print("Goodbye")
                return
            
            else:
                print ("Invalid option")

        except (ValidationError, NotFoundError) as e:
            print (f"Error: {e}")

        except Exception as e:
            print (f"Unexpected error: {e}")

if __name__ == "__main__":
    menu()