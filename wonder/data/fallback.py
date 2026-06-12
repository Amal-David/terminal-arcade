"""Curated offline fallback content per category.

Used when the internet fetch fails. Each entry maps to the Story shape used by
the fetcher. Picks are deterministic per (date, category) so the same offline
day yields the same fallback.
"""

from __future__ import annotations

FUNNY = [
    {"title": "Dad joke", "body": "I'm reading a book on anti-gravity. It's impossible to put down.", "source": "Bundled"},
    {"title": "Dad joke", "body": "I told my wife she was drawing her eyebrows too high. She looked surprised.", "source": "Bundled"},
    {"title": "Dad joke", "body": "Why don't scientists trust atoms? Because they make up everything.", "source": "Bundled"},
    {"title": "Dad joke", "body": "I would tell you a construction joke, but I'm still working on it.", "source": "Bundled"},
    {"title": "Dad joke", "body": "Parallel lines have so much in common — it's a shame they'll never meet.", "source": "Bundled"},
    {"title": "Dad joke", "body": "I used to play piano by ear, but now I use my hands.", "source": "Bundled"},
    {"title": "Dad joke", "body": "Why did the scarecrow win an award? Because he was outstanding in his field.", "source": "Bundled"},
    {"title": "Dad joke", "body": "I'm on a seafood diet. I see food and I eat it.", "source": "Bundled"},
    {"title": "Dad joke", "body": "What do you call cheese that isn't yours? Nacho cheese.", "source": "Bundled"},
    {"title": "Dad joke", "body": "I'm terrified of elevators, so I'm going to start taking steps to avoid them.", "source": "Bundled"},
    {"title": "Dad joke", "body": "Why don't skeletons fight each other? They don't have the guts.", "source": "Bundled"},
    {"title": "Dad joke", "body": "I asked the librarian if the library had books on paranoia. She whispered, 'They're right behind you.'", "source": "Bundled"},
    {"title": "Dad joke", "body": "Did you hear about the mathematician who's afraid of negative numbers? He'll stop at nothing to avoid them.", "source": "Bundled"},
    {"title": "Dad joke", "body": "I bought shoes from a drug dealer. I don't know what he laced them with, but I was tripping all day.", "source": "Bundled"},
    {"title": "Dad joke", "body": "What's orange and sounds like a parrot? A carrot.", "source": "Bundled"},
]

HEARTWARMING = [
    {"title": "A small kindness", "body": "A barista in Seattle started a 'pay it forward' chain at her drive-through that ran for 11 hours, with 458 customers each buying coffee for the car behind them before someone finally broke the streak.", "source": "Bundled"},
    {"title": "Lost dog reunion", "body": "After being missing for two years, a golden retriever named Cleo turned up at the door of her old family home — 57 miles from where she had been lost. Vets confirmed it was her by microchip.", "source": "Bundled"},
    {"title": "Stranger's note", "body": "A teenager who stopped a stranger from jumping off a bridge later got an unexpected letter — the man's daughter, born a year after, wrote to thank him for her father's life.", "source": "Bundled"},
    {"title": "Library that listens", "body": "A small library in rural Sweden invites people to 'borrow' a person for a 30-minute conversation — a refugee, a retired sailor, a teen activist — to break stereotypes one tea at a time.", "source": "Bundled"},
    {"title": "The marathon assist", "body": "When a Spanish runner was about to overtake him in the final stretch, Kenyan athlete Abel Mutai stopped early thinking he had crossed the line. The runner behind him slowed down, gestured, and guided him to the finish.", "source": "Bundled"},
    {"title": "Free fridge", "body": "A street corner in Queens has had a 'community fridge' running 24/7 since 2020 — anyone can leave food, anyone can take food, no questions asked. Volunteers say it's never once been empty.", "source": "Bundled"},
    {"title": "Letters in bottles", "body": "A retired postman in Cornwall has spent 30 years answering messages found in bottles washed ashore — over 1,200 replies, in 14 languages, sometimes typed on his old typewriter.", "source": "Bundled"},
    {"title": "Unexpected scholarship", "body": "After a janitor at a Boston public school passed away, the community discovered he had quietly funded a college scholarship for the school's students every year for two decades, anonymously.", "source": "Bundled"},
    {"title": "Train hero", "body": "When a man fell onto subway tracks and seizured, Wesley Autrey jumped down and pinned him in the gap between the rails as a train passed inches above their heads. He went back to picking up his daughters from daycare like nothing happened.", "source": "Bundled"},
    {"title": "Birthday surprise", "body": "An 8-year-old wrote letters to every house on her street inviting her elderly neighbor to her birthday party because she 'looked lonely.' 47 strangers showed up with gifts.", "source": "Bundled"},
    {"title": "Forgotten violin", "body": "A street musician played the same Bach piece every morning at a metro station for 6 years. When he finally retired, commuters chipped in to buy him a real concert hall ticket — and one of them turned out to be a violin maker who built him a custom instrument.", "source": "Bundled"},
    {"title": "Hospital window", "body": "Children in a pediatric ward in Lyon look out their windows to see window-washers dressed as superheroes rappelling down the building twice a week — a tradition started by one welder whose niece was once on that floor.", "source": "Bundled"},
]

WEIRD = [
    {"title": "Did you know?", "body": "A group of flamingos is called a 'flamboyance.' A group of ferrets is called a 'business.' And a group of hippos is called a 'bloat.'", "source": "Bundled"},
    {"title": "Did you know?", "body": "Octopuses have three hearts, nine brains, and blue blood. Two of the hearts pump blood through the gills, while the third pumps it through the rest of the body.", "source": "Bundled"},
    {"title": "Did you know?", "body": "A day on Venus is longer than a year on Venus. Venus rotates so slowly that it takes 243 Earth days to complete one rotation, but only 225 Earth days to orbit the Sun.", "source": "Bundled"},
    {"title": "Did you know?", "body": "Honey never spoils. Archaeologists have found pots of honey in ancient Egyptian tombs that are over 3,000 years old and still perfectly edible.", "source": "Bundled"},
    {"title": "Did you know?", "body": "Bananas are berries, but strawberries aren't. Botanically, a berry must come from a single ovary of a single flower with multiple seeds inside.", "source": "Bundled"},
    {"title": "Did you know?", "body": "There are more possible iterations of a chess game than there are atoms in the observable universe — about 10^120 versus 10^80.", "source": "Bundled"},
    {"title": "Did you know?", "body": "Wombat poop is cube-shaped. Their intestines compress waste into roughly cube blocks so it doesn't roll away from the rocks they use as territory markers.", "source": "Bundled"},
    {"title": "Did you know?", "body": "The Eiffel Tower can grow more than 6 inches taller in summer due to thermal expansion of the iron.", "source": "Bundled"},
    {"title": "Did you know?", "body": "Sharks existed before trees. Sharks have been around for about 400 million years, while the earliest trees appeared around 350 million years ago.", "source": "Bundled"},
    {"title": "Did you know?", "body": "A cloud weighs around 1.1 million pounds on average. Despite this, they stay aloft because that mass is spread across cubic kilometres of warm rising air.", "source": "Bundled"},
    {"title": "Did you know?", "body": "If you somehow folded a piece of paper 42 times, it would reach the Moon. The thickness doubles each fold — by 23 folds it's a kilometer thick.", "source": "Bundled"},
    {"title": "Did you know?", "body": "Cleopatra lived closer in time to the Moon landing than to the construction of the Great Pyramid of Giza.", "source": "Bundled"},
    {"title": "Did you know?", "body": "The shortest war in history was between Britain and Zanzibar in 1896 — it lasted just 38 minutes.", "source": "Bundled"},
    {"title": "Did you know?", "body": "Sloths can hold their breath underwater for up to 40 minutes by slowing their heart rate to one-third of normal — longer than most dolphins.", "source": "Bundled"},
    {"title": "Did you know?", "body": "Your brain can survive 5–10 minutes without oxygen, but a tardigrade can survive in the vacuum of outer space for 10 days.", "source": "Bundled"},
]

INSPIRING = [
    {"title": "Late bloomer", "body": "Vera Wang didn't start designing dresses until she was 40. Colonel Sanders started Kentucky Fried Chicken at 65. Grandma Moses didn't start painting until she was 78 — and went on to produce 1,500 works.", "source": "Bundled"},
    {"title": "From rejection", "body": "J.K. Rowling's Harry Potter manuscript was rejected by 12 publishers before Bloomsbury accepted it — and only then because the chairman's 8-year-old daughter begged him to publish it.", "source": "Bundled"},
    {"title": "Quiet persistence", "body": "Stephen Hawking was given two years to live at age 21. He wrote his most famous book 25 years later, traveled in zero gravity at 65, and lived to 76.", "source": "Bundled"},
    {"title": "The walking man", "body": "After losing both legs in an accident, Terry Fox set out to run across Canada on a prosthetic leg to raise money for cancer research. He ran a marathon a day for 143 days, covering 5,373 km before being forced to stop.", "source": "Bundled"},
    {"title": "Late start", "body": "Julia Child didn't write her first cookbook until she was 50, and didn't host her first TV show until 51. She kept cooking on television into her 90s.", "source": "Bundled"},
    {"title": "Builder", "body": "Mary Anderson invented the windshield wiper in 1903 after watching a streetcar driver struggle with sleet. Her patent was rejected as 'commercially unviable.' Today every car on Earth has one.", "source": "Bundled"},
    {"title": "One step", "body": "Jadav Payeng has been planting one tree a day on a barren sandbar in India since 1979. The Molai Forest he created is now larger than Central Park, home to tigers, elephants, and rhinos.", "source": "Bundled"},
    {"title": "Self-taught", "body": "Srinivasa Ramanujan had almost no formal training in mathematics. Working alone in poverty in India, he independently rediscovered theorems that had taken European mathematicians centuries — and produced new ones still being unraveled today.", "source": "Bundled"},
    {"title": "Quiet revolution", "body": "Rosa Parks didn't refuse to give up her seat on impulse. She had spent over a decade as the secretary of her local NAACP chapter, training in nonviolent resistance, before that single moment changed history.", "source": "Bundled"},
    {"title": "Re-reading the script", "body": "Nick Vujicic was born without arms or legs. After years of depression, he decided to learn to swim, surf, and skydive — and now travels the world giving talks. He once said, 'If I fail, I try again, and again, and again.'", "source": "Bundled"},
    {"title": "Failed forward", "body": "Thomas Edison made over 1,000 unsuccessful attempts at inventing the light bulb. When asked how it felt to fail so many times, he said: 'I didn't fail. I just found 1,000 ways that didn't work.'", "source": "Bundled"},
    {"title": "Marathon at 100", "body": "Fauja Singh ran his first marathon at 89 and his last one at 101. He took up running to cope with grief after losing his wife and son.", "source": "Bundled"},
]

FALLBACKS = {
    "funny": FUNNY,
    "heartwarming": HEARTWARMING,
    "weird": WEIRD,
    "inspiring": INSPIRING,
}
