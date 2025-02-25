import csv
import statistics

from collections import defaultdict
from typing import Any, Dict, List

from limbic.emotion.utils import load_lexicon
from limbic.limbic_types import Emotion, Lexicon

# This application/product/tool makes use of the NRC Word-Emotion Association Lexicon,
# created by Saif M. Mohammad and Peter D. Turney at the National Research Council Canada,
# the NRC Valence, Arousal, Dominance Lexicon, created by Saif M. Mohammad
# at the National Research Council Canada, and the NRC Affect Intensity Lexicon,
# created by Saif M. Mohammad at the National Research Council Canada.

# You can check more details and get the emotion lexicon files in the following links
# http://saifmohammad.com/WebPages/AccessResource.htm
# and http://saifmohammad.com/WebPages/lexicons.html


class NotValidNRCLexiconException(Exception):
    pass


def is_float(element: Any) -> bool:
    try:
        float(element)
        return True
    except ValueError:
        return False


def load_nrc_lexicon(lexicon_path: str, lexicon_type: str) -> Lexicon:
    if lexicon_type == 'emotion':
        return _load_nrc_emotion(lexicon_path)
    if lexicon_type == 'affect_intensity':
        return _load_nrc_affect_intensity(lexicon_path)
    if lexicon_type == 'vad':
        return _load_nrc_vad(lexicon_path)
    raise NotValidNRCLexiconException


def _load_nrc_emotion(lexicon_file_path: str) -> Lexicon:
    return load_lexicon(lexicon_file_path)


def load_nrc_multilingual(multi_lingual_file_path: str, language: str) -> Lexicon:
    """
    Load NRC multi-lingual mapping.

    Note that this is hardcoded to core 4 emotions: joy, anger, fear, sadness
    """
    data: Dict[str, List[Emotion]] = defaultdict(list)
    categories = set()
    with open(multi_lingual_file_path, 'r') as emotions_mapping_file:
        reader = csv.DictReader(emotions_mapping_file, delimiter='\t')
        for line in reader:
            term = line.get(language)
            for emotion in ['joy', 'fear', 'anger', 'sadness']:
                score = float(line.get(emotion, 0))
                if score > 0:
                    data[term].append(Emotion(value=score, category=emotion, term=term))
                    categories.add(emotion)
    aggregated_data = _aggregate_emotions(data)
    return Lexicon(emotion_mapping=aggregated_data, categories=categories)


def _aggregate_emotions(input_data: Dict[str, List[Emotion]]) -> Dict[str, List[Emotion]]:
    """
    If a term has multiple scores for an emotion, keep the average score.

    In the NRC multi-lingual mapping is common that a term could be associated to multiple translations, for example
    "encouragement" and "zest" both translate to "ánimo" in Spanish.
    """
    data: Dict[str, List[Emotion]] = defaultdict(list)
    for term, emotions in input_data.items():
        emotion_scores = defaultdict(list)
        for emotion in emotions:
            emotion_scores[emotion.category].append(emotion.value)
        for emotion, values in emotion_scores.items():
            data[term].append(Emotion(value=statistics.mean(values), category=emotion, term=term))
    return data


def _load_nrc_affect_intensity(lexicon_file_path: str) -> Lexicon:
    """
    As described in https://saifmohammad.com/WebPages/AffectIntensity.htm
        The lexicon has close to 6,000 entries for four basic emotions: anger, fear, joy, and sadness.
    """
    data: Dict[str, List[Emotion]] = defaultdict(list)
    categories = set()
    with open(lexicon_file_path, 'r') as intensity_file:
        for line in intensity_file.readlines():
            line_split = line.strip().split('\t')
            if is_float(line_split[1]):
                term, score, affect_dimension = line_split
                data[term].append(Emotion(value=float(score), category=affect_dimension, term=term))
                categories.add(affect_dimension)
            elif is_float(line_split[2]):
                term, affect_dimension, score = line_split
                data[term].append(Emotion(value=float(score), category=affect_dimension, term=term))
                categories.add(affect_dimension)
            else:
                continue
    return Lexicon(emotion_mapping=data, categories=categories)


def _load_nrc_vad(lexicon_file_path) -> Lexicon:
    """
    As described in https://saifmohammad.com/WebPages/nrc-vad.html
        valence is the positive--negative or pleasure--displeasure dimension;
        arousal is the excited--calm or active--passive dimension; and
        dominance is the powerful--weak or 'have full control'--'have no control' dimension.
    """
    data: Dict[str, List[Emotion]] = defaultdict(list)
    with open(lexicon_file_path, 'r') as vad_file:
        for idx, line in enumerate(vad_file.readlines()):
            if idx > 0:
                term, valence, arousal, dominance = line.strip().split('\t')
                data[term].append(Emotion(value=float(valence), category='valence', term=term))
                data[term].append(Emotion(value=float(arousal), category='arousal', term=term))
                data[term].append(Emotion(value=float(dominance), category='dominance', term=term))
    return Lexicon(emotion_mapping=data, categories={'valence', 'arousal', 'dominance'})
