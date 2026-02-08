from unreal_api_extractor.normalizer import normalize_unreal_macro


def test_normalize_macro():
    assert normalize_unreal_macro("UCLASS(BlueprintType)") == "[[ue::UCLASS(BlueprintType)]]"
