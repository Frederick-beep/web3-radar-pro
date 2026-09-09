from app.services.scoring import wallet_score, token_score, alpha_score
def test_scores():
    assert 0 <= wallet_score(20,5,12,8,2) <= 100
    assert 0 <= token_score(100,50,2,3,100000,200000) <= 100
    assert alpha_score(5,3,100,50,200000,500000) >= 70
