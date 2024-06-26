from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Refined trait names
trait_names = {
    "Introversion/Extraversion": ["Introverted", "Extraverted"],
    "Thinking/Feeling": ["Thinking", "Feeling"],
    "Sensing/Intuition": ["Sensing", "Intuitive"],
    "Judging/Perceiving": ["Judging", "Perceiving"],
    "Conscientiousness": ["Careless", "Conscientious"],
    "Agreeableness": ["Disagreeable", "Agreeable"],
    "Neuroticism": ["Non-Neurotic", "Neurotic"],
    "Individualism/Collectivism": ["Individualistic", "Collectivistic"],
    "Libertarianism/Authoritarianism": ["Libertarian", "Authoritarian"],
    "Environmentalism/Anthropocentrism": ["Environmental", "Anthropocentric"],
    "Isolationism/Internationalism": ["Isolationist", "Internationalist"],
    "Security/Freedom": ["Security-focused", "Freedom-focused"],
    "Non-interventionism/Interventionism": ["Non-Interventionist", "Interventionist"],
    "Equity/Meritocracy": ["Equity-focused", "Meritocracy-focused"],
    "Empathy": ["Indifferent", "Empathetic"],
    "Honesty": ["Dishonest", "Honest"],
    "Humility": ["Proud", "Humble"],
    "Independence": ["Dependent", "Independent"],
    "Patience": ["Impatient", "Patient"],
    "Persistence": ["Inconsistent", "Persistent"],
    "Playfulness": ["Serious", "Playful"],
    "Rationality": ["Irrational", "Rational"],
    "Religiosity": ["Secular", "Religious"],
    "Self-acceptance": ["Self-Critical", "Self-Accepting"],
    "Sex Focus": ["Non-Sex-Focused", "Sex-Focused"],
    "Thriftiness": ["Generous", "Frugal"],
    "Thrill-seeking": ["Cautious", "Thrill-seeking"],
    "Drug Friendliness": ["Drug-averse", "Drug-friendly"],
    "Emotional Openness in Relationships": ["Reserved", "Emotionally Open"],
    "Equanimity": ["Reactive", "Equanimous"],
    "Family Focus": ["Individual-focused", "Family-focused"],
    "Loyalty": ["Disloyal", "Loyal"],
    "Preference for Monogamy": ["Non-Monogamous", "Monogamous"],
    "Trust": ["Distrustful", "Trusting"],
    "Self-esteem": ["Low Self-esteem", "High Self-esteem"],
    "Anxious Attachment": ["Not Anxious", "Anxious"],
    "Avoidant Attachment": ["Not Avoidant", "Avoidant"],
    "Career Focus": ["Not Career-focused", "Career-focused"],
    "Emphasis on Boundaries": ["Flexible Boundaries", "Firm Boundaries"],
    "Fitness Focus": ["Not Fitness-focused", "Fitness-focused"],
    "Stability of Self-image": ["Unstable Self-Image", "Stable Self-Image"],
    "Love Focus": ["Love-averse", "Love-focused"],
    "Maturity": ["Immature", "Mature"],
    "Wholesomeness": ["Unwholesome", "Wholesome"],
    "Traditionalism about Love": ["Non-Traditional", "Traditional"],
    "Openness to Experience": ["Closed to Experience", "Open to Experience"]
}

class UserAnswers(BaseModel):
    answers: Dict[str, bool]


class ScoreKeeper:

    weights: dict

    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(ScoreKeeper, cls).__new__(cls)
            cls.instance._load_weights()
        return cls.instance


    def _load_weights(self) -> Dict | None:
        try:
            with open('./scores.json', 'r') as f:
                self.weights = json.load(f)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    def _calculate_trait_scores(self, user_answers: Dict[str, bool], questions_scores: Dict[str, Any]) -> Dict[str, float]:
        traits_scores = {trait: {'cumulative_score': 0.0, 'count': 0} for question in questions_scores.values() for trait in question.keys()}
        
        for question, answer in user_answers.items():
            if question in questions_scores:
                for trait, scores in questions_scores[question].items():
                    presence_score = scores['presence_given_yes'] if answer else scores['presence_given_no']
                    traits_scores[trait]['cumulative_score'] += presence_score
                    traits_scores[trait]['count'] += 1
        
        normalized_scores = {}
        for trait, data in traits_scores.items():
            if data['count'] > 0:
                raw_score = data['cumulative_score'] / data['count']
                weight = 4
                if raw_score > 0.5:
                    weighted_score = 0.5 + (raw_score - 0.5) * weight
                else:
                    weighted_score = 0.5 - (0.5 - raw_score) * weight
                normalized_score = min(max(weighted_score, 0.0), 1.0)
            else:
                normalized_score = 0.0
            normalized_scores[trait] = normalized_score

        return normalized_scores

    def calculate_individual(self, user_answers: Dict[str, bool], questions_scores: Dict[str, Any]) -> Dict[str, float]:
        return self._calculate_trait_scores(user_answers, questions_scores)


@app.post("/calculate_scores/individual")
def calculate_scores(user_answers: UserAnswers):
    try:
        logger.info(f"Received answers: {user_answers.answers}")
        if not user_answers.answers:
            raise ValueError("Answers cannot be empty")
        sk = ScoreKeeper()
        normalized_scores = sk.calculate_individual(user_answers.answers, sk.instance.weights)
        logger.info(f"Calculation result: {normalized_scores}")
        return {"traits_scores": normalized_scores}
    except ValueError as ve:
        logger.error(f"ValueError: {ve}")
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))