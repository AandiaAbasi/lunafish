"""Seed realistic fictional reviews on a PRESENTATION instance only.

All reviews here are authored sample content, not genuine student feedback.
They have natural public-facing text; their synthetic nature is recorded in
the internal account username prefix and this command's source. Only use
where the presentation itself is disclosed as illustrative.

Usage:
    python manage.py seed_catalog_presentation_reviews
    python manage.py seed_catalog_presentation_reviews --apply --confirm-presentation
    python manage.py seed_catalog_presentation_reviews --remove --confirm-presentation
"""
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from account.models import TeacherRating, User


# Source: lunafish_english_catalog(2).json
CATALOG_USERNAMES = {9300001:"olivia.hartley",9300002:"daniel.whitmore",9300003:"maya.bennett",9300004:"lucas.reed",9300005:"camille.laurent",9300006:"julien.moreau",9300007:"elise.fournier",9300008:"giulia.romano",9300009:"matteo.ricci",9300010:"sofia.bellini",9300011:"lucia.navarro",9300012:"mateo.alvarez",9300013:"isabel.ortega",9300014:"lena.fischer",9300015:"tobias.weber",9300016:"clara.hoffmann",9300017:"yuki.tanaka",9300018:"haruto.sato",9300019:"minseo.park",9300020:"jihoon.kim",9300021:"mei.lin",9300022:"chen.wei",9300023:"beatriz.costa",9300024:"rafael.oliveira"}

# One 1-to-5-star score and one original, educator-specific comment per author.
PRESENTATION_REVIEWS = {9300001:[[5,"Olivia explained the difference between sounds I kept mixing up. The practice was simple enough to use every day."],[4,"I liked how much time we spent actually speaking instead of just reading rules. A little more homework would be nice."],[5,"The pronunciation notes were specific and easy to remember. I feel much less hesitant during short conversations."],[4,"Clear explanations and a calm pace. The short speaking drills worked well for me."]],9300002:[[5,"The meeting role-plays felt close to situations I deal with at work. I picked up several phrases I now use regularly."],[4,"Daniel gave practical feedback on how to structure my presentations. I would have liked a few more examples."],[5,"My main goal was sounding more confident in client calls, and the exercises stayed focused on that."],[4,"Very organized sessions, especially the work on transitions between presentation points."]],9300003:[[5,"Maya helped me stop translating every sentence in my head when I read. The short stories made practice enjoyable."],[4,"I appreciated the mix of reading and discussion. Some of the vocabulary was challenging, but manageable."],[5,"Her questions made me notice details I usually missed in a text. Great approach for improving comprehension."],[4,"The storytelling exercises gave me a comfortable way to speak for longer without memorizing lines."]],9300004:[[5,"The discussions pushed me to explain my opinions more precisely. I came away with vocabulary I actually wanted to use."],[4,"Good balance between correction and open conversation. The reading selections can be quite demanding."],[5,"Lucas asked thoughtful follow-up questions rather than letting me give one-word answers."],[4,"I liked the vocabulary work, particularly how we practiced new expressions in real arguments."]],9300005:[[5,"The way Camille broke down French nasal vowels finally made them understandable to me."],[4,"Speaking practice was helpful, especially the everyday dialogues. I still need more repetition on some sounds."],[5,"Very patient corrections without interrupting the flow of conversation too much."],[4,"Useful pronunciation tips and a friendly pace. I felt comfortable trying new phrases."]],9300006:[[5,"The listening tasks used situations I might really face while traveling. That made them easy to remember."],[4,"I enjoyed practicing directions and ordering food in French. The recordings sometimes took a second listen."],[5,"Julien showed me how to catch key words rather than panic when I missed a full sentence."],[4,"Practical lessons and plenty of speaking time. I especially liked the travel scenarios."]],9300007:[[5,"Elise helped me understand why a sentence works stylistically, not just whether it's grammatically correct."],[4,"The reading material was challenging in a good way. I needed extra time for some passages."],[5,"Her comments on my writing were precise and made revising much easier."],[4,"A thoughtful approach to literary French with good attention to nuance and tone."]],9300008:[[5,"Giulia made everyday Italian feel approachable. The cultural examples gave the expressions much more context."],[4,"I liked the conversational focus. I would enjoy a slightly longer vocabulary recap at the end."],[5,"The practice conversations felt natural rather than like memorized textbook dialogues."],[4,"Warm teaching style and useful phrases for real-life situations."]],9300009:[[5,"Matteo clarified several grammar points I had been guessing at for ages. The examples were really practical."],[4,"Helpful explanations of verb forms and sentence structure. There was a lot to absorb in one session."],[5,"The business-focused exercises were exactly what I needed for emails and short conversations."],[4,"Structured lessons with clear corrections. I appreciated the focus on using the grammar immediately."]],9300010:[[5,"Sofia made my first Italian conversations much less intimidating. She explained each sound clearly."],[4,"A comfortable pace for a complete beginner. More quick review quizzes would be useful."],[5,"The pronunciation exercises were fun and easy to repeat between lessons."],[4,"Clear, friendly teaching and a good mix of listening and simple speaking."]],9300011:[[5,"Lucia helped me sound less stiff when speaking Spanish. The rhythm exercises made a noticeable difference."],[4,"The conversation prompts were useful and varied. I sometimes wanted a bit more time to prepare."],[5,"I finally understand where to stress words in longer sentences. Her examples were very clear."],[4,"Relaxed atmosphere with plenty of practice for everyday conversations."]],9300012:[[5,"The storytelling approach helped me use past tenses without stopping to think about every ending."],[4,"Mateo explained verb patterns patiently. Some exercises were difficult, but they made sense afterward."],[5,"I liked turning small everyday stories into longer conversations. It helped me find words faster."],[4,"Practical feedback and a clear progression from short answers to complete stories."]],9300013:[[5,"Isabel's feedback on my Spanish essays was direct and very detailed. I knew exactly what to revise."],[4,"The debate topics were interesting and pushed my vocabulary. Preparation took more time than I expected."],[5,"I became more confident defending an opinion in Spanish instead of relying on simple phrases."],[4,"Strong focus on argument structure and precise wording. Good for advanced learners."]],9300014:[[5,"German word order finally started making sense after Lena showed the patterns side by side."],[4,"The workplace examples were useful. I would appreciate some additional written practice afterward."],[5,"She corrected my sentence structure without making conversation feel like a grammar test."],[4,"Clear lessons and helpful phrases for meetings and everyday office conversations."]],9300015:[[5,"Tobias showed me how to approach longer listening sections without trying to understand every word."],[4,"Very useful exam-style practice. The pace was intense at times, but the feedback helped."],[5,"The listening strategies were easy to apply in my next mock exam."],[4,"Well-organized lessons with a sensible balance of exercises and explanations."]],9300016:[[5,"Clara focused on exactly the German phrases I needed for daily errands. The practice felt immediately useful."],[4,"I enjoyed the travel scenarios and the patient corrections. Some dialogues could have been a little longer."],[5,"The role-plays helped me feel prepared for simple conversations outside the classroom."],[4,"A friendly approach to practical German, with clear examples and manageable homework."]],9300017:[[5,"Yuki explained the writing systems in a way that made learning characters feel less overwhelming."],[4,"I liked the step-by-step writing practice. Remembering the characters still takes consistent work."],[5,"The polite expression examples were especially helpful because the context was explained too."],[4,"Careful teaching and useful corrections on writing and pronunciation."]],9300018:[[5,"Haruto's listening exercises helped me pick out common Japanese phrases at normal speed."],[4,"Good real-life dialogues. Some recordings were fast for my level, but we worked through them."],[5,"I learned when to use more casual expressions and when to keep things polite."],[4,"The sentence patterns were introduced naturally through conversation."]],9300019:[[5,"Minseo helped me hear distinctions between Korean sounds that seemed identical before."],[4,"The speaking drills were effective. I needed to repeat some of them quite a few times."],[5,"Pronunciation feedback was gentle but very specific, which made practicing alone easier."],[4,"Useful everyday expressions and a comfortable amount of speaking practice."]],9300020:[[5,"Jihoon made formal Korean endings much easier to understand by comparing real situations."],[4,"The explanations were clear, though I wanted a few more examples of informal alternatives."],[5,"I liked the focus on building whole sentences instead of memorizing isolated words."],[4,"Well-paced grammar practice with useful corrections and speaking exercises."]],9300021:[[5,"Mei's tone exercises made a big difference. She helped me notice mistakes I couldn't hear on my own."],[4,"Very clear pronunciation coaching. Keeping the tones consistent still takes effort."],[5,"The short dialogues were practical and gave me more confidence speaking Mandarin aloud."],[4,"Patient explanations and plenty of chances to repeat sounds in context."]],9300022:[[5,"Chen showed me patterns in Chinese characters that made them easier to remember."],[4,"I enjoyed the writing exercises, although some character groups required extra practice."],[5,"The lesson connected reading, writing and simple conversation rather than treating them separately."],[4,"Good structure and helpful examples for forming more natural Mandarin sentences."]],9300023:[[5,"Beatriz explained European Portuguese pronunciation so clearly that the listening practice became much easier."],[4,"The everyday dialogues were useful. I would have liked a few more slower audio examples."],[5,"I appreciated learning which expressions sound natural in Portugal rather than only textbook phrases."],[4,"Friendly lessons with a good balance of pronunciation and useful conversation."]],9300024:[[5,"Rafael helped me follow longer Portuguese conversations without losing the main idea."],[4,"The advanced listening tasks were challenging, but we discussed them carefully afterward."],[5,"I liked the focus on understanding tone and implied meaning, not just vocabulary."],[4,"Thoughtful feedback and plenty of practice responding to longer questions."]]}
FIRST_NAMES = ["Emma","Noah","Sophie","Liam","Ava","Ethan","Mia","Oliver","Chloe","Leo","Grace","Daniel","Isla","Adam","Ruby","Jacob","Hannah","Oscar","Zoe","Nathan","Amelia","Ryan","Nina","Alex","Lily","Aria","Samuel","Evelyn","Lucas","Ella","Max","Sara","Theo","Leah","Owen","Maya","Elena","Ben","Emily","Aaron","Jade","David","Clara","Anna","James","Nora","Felix","Lucy"]
LAST_NAMES = ["Turner","Walsh","Martin","Collins","Morgan","Hill","Bennett","Ross","Hayes","Parker","Brooks","Reed","Morris","Foster","Evans","Price","Cooper","Bell","Bailey","Gray","Carter","Hughes","Mason","Phillips","Woods","Ward","Kelly","Cook","Green","Richardson","Stone","Harris","Howard","Diaz","Peterson","Murray","Wright","Young","Adams","Russell","Taylor","Nguyen","King","Clark","Rivera","Campbell","Baker","Scott"]
INTERNAL_PREFIX = "lunafish_presentation_reviewer_"


class Command(BaseCommand):
    help = "Preview or seed natural-looking fictional catalog reviews on a presentation instance"

    def add_arguments(self, parser):
        parser.add_argument("--apply", action="store_true", help="Insert fictional presentation reviews")
        parser.add_argument("--remove", action="store_true", help="Remove only ratings inserted by this command")
        parser.add_argument(
            "--confirm-presentation", action="store_true",
            help="Confirm this dataset is being used for an explicitly illustrative project presentation",
        )

    def handle(self, *args, **options):
        apply = options["apply"]
        remove = options["remove"]
        if apply and remove:
            raise CommandError("Use either --apply or --remove, not both")
        if (apply or remove) and not options["confirm_presentation"]:
            raise CommandError("Use --confirm-presentation only on an illustrative presentation instance")

        teachers = {}
        for teacher_id, expected_username in CATALOG_USERNAMES.items():
            teacher = User.objects.filter(pk=teacher_id, role="teacher", username=expected_username).first()
            if teacher is None:
                raise CommandError(f"Catalog teacher {teacher_id} ({expected_username}) not found")
            teachers[teacher_id] = teacher

        self.stdout.write(
            f"Validated {len(teachers)} teachers and "
            f"{sum(len(reviews) for reviews in PRESENTATION_REVIEWS.values())} presentation reviews."
        )
        if not (apply or remove):
            self.stdout.write("Preview only: no database changes. Use --apply --confirm-presentation.")
            return

        if remove:
            with transaction.atomic():
                deleted, _ = TeacherRating.objects.filter(
                    teacher_id__in=CATALOG_USERNAMES,
                    rater__username__startswith=INTERNAL_PREFIX,
                ).delete()
            self.stdout.write(f"Deleted {deleted} internal presentation rating rows.")
            return

        created_ratings = 0
        with transaction.atomic():
            for teacher_index, (teacher_id, reviews) in enumerate(PRESENTATION_REVIEWS.items()):
                teacher = teachers[teacher_id]
                for index, (stars, comment) in enumerate(reviews):
                    n = teacher_index * 4 + index
                    username = f"{INTERNAL_PREFIX}{n + 1:03d}"
                    display_name = f"{FIRST_NAMES[n % len(FIRST_NAMES)]} {LAST_NAMES[(n * 7 + 3) % len(LAST_NAMES)]}"
                    rater, created_user = User.objects.get_or_create(
                        username=username,
                        defaults={
                            "name": display_name,
                            "first_name": display_name.split(" ", 1)[0],
                            "last_name": display_name.split(" ", 1)[1],
                            "role": "user",
                            "is_active": False,
                        },
                    )
                    if created_user:
                        rater.set_unusable_password()
                        rater.save(update_fields=["password"])
                    elif (
                        rater.role != "user"
                        or rater.is_active
                        or rater.has_usable_password()
                        or rater.name != display_name
                    ):
                        raise CommandError(f"Conflicting account: {username}. No reviews were inserted.")
                    _, created_rating = TeacherRating.objects.get_or_create(
                        teacher=teacher,
                        rater=rater,
                        defaults={
                            "stars": stars,
                            "comment": comment,
                            "rater_type": "student",
                            "is_anonymous": False,
                            "is_verified": True,
                        },
                    )
                    if created_rating:
                        created_ratings += 1
        self.stdout.write(
            self.style.SUCCESS(f"Created {created_ratings} presentation ratings; existing records untouched.")
        )
