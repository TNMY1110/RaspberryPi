from flask import Flask, request,jsonify
from flask.json.provider import DefaultJSONProvider
import json

class CustomJSONProvider(DefaultJSONProvider):
    def default(self, obj):
        if isinstance(obj, set):
            return list(obj)

        return super().default(obj)

app = Flask(__name__)
app.users = {}
app.id_count = 1
app.tweets = []
app.tweet_id_count = 1      # 트윗 아이디 추가
app.json_provider_class = CustomJSONProvider
app.json = CustomJSONProvider(app)


@app.route("/ping", methods=['GET'])

def ping():
    return "pong"

@app.route("/sign-up", methods=['POST'])
def sign_up():
    new_user = request.json                 # 회원정보 읽기
    new_user["id"] = app.id_count
    app.users[app.id_count] = new_user
    app.id_count = app.id_count + 1

    return jsonify(new_user)                # json형태로 전송 

@app.route('/tweet', methods=['POST'])
def tweet():
    payload = request.json
    user_id = int(payload['id'])
    tweet = payload['tweet']
    like = []

    if user_id not in app.users:
        return '사용자가 존재하지 않습니다.', 400

    if len(tweet) > 300:
        return '300자를 초과했습니다.', 400

    app.tweets.append({
        'user_id' : user_id,
        'tweet' : tweet,
        'tweet_id' : app.tweet_id_count,
        'like' : like
    })

    app.tweet_id_count = app.tweet_id_count + 1     // 트윗 아이디 카운트 더하기

    return '', 200

@app.route('/follow', methods=['POST'])
def follow():
    payload = request.json
    user_id = int(payload['id'])
    user_id_to_follow = int(payload['follow'])

    if user_id == user_id_to_follow:
        return '본인은 팔로우 할 수 없습니다.', 400

    if user_id not in app.users or user_id_to_follow not in app.users:
        return '사용자가 존재하지 않습니다.', 400

    user = app.users[user_id]
    user.setdefault('follow', set()).add(user_id_to_follow) #키가 존재하지 않으면 디폴트값을 저장하고, 만일 키가 이미 존재하면 해당 값을 읽어들이는 기능 

    return jsonify(user)

@app.route('/unfollow', methods=['POST'])
def unfollow():
    payload = request.json
    user_id = int(payload['id'])
    user_id_to_unfollow = int(payload['follow'])

    if user_id not in app.users or user_id_to_unfollow not in app.users:
        return '사용자가 존재하지 않습니다.', 400

    user = app.users[user_id]

    if 'follow' in user:        # 언팔로우 시에는 없는 저장 공간을 새로 만들기보다, 팔로우 목록이 없으면 그냥 무시
        user['follow'].discard(user_id_to_unfollow)

    return jsonify(user)

@app.route('/timeline/<int:user_id>', methods=['GET'])
def timeline(user_id):
    if user_id not in app.users:
        return '사용자가 존재하지 않습니다.', 400

    follow_list = app.users[user_id].get('follow', set())
    follow_list.add(user_id)
    timeline = [tweet for tweet in app.tweets if tweet['user_id'] in follow_list]

    return jsonify({
        'user_id' : user_id,
        'timeline' : timeline
    })

# 유저 정보 조회 API
# GET /user/<int:user_id> 엔드포인트 추가
# 해당 유저의 정보를 JSON으로 반환
# 존재하지 않는 유저 요청 시 400 에러 반환
# http GET localhost:5000/user/1

@app.route('/user/<int:user_id>', methods=['GET'])
def userinfo(user_id):
    if user_id not in app.users:
        return '사용자가 존재하지 않습니다.', 400

    username = app.users[user_id].get('name', set())
    useremail = app.users[user_id].get('email', set())

    return jsonify({
        'user_id' : user_id,
        'name' : username,
        'email' : useremail
    })

# 전체 유저 목록 조회
# GET /users 엔드포인트 추가
# 가입된 모든 유저 목록을 JSON 배열로 반환
# 단, password는 제외하고 반환할 것

@app.route('/users', methods=['GET'])
def allusersinfo():
    users_list = [{key:val for key, val in user.items() if key != 'password'} for user in app.users.values()]

    return jsonify(users_list)

# 트윗 삭제 기능
# DELETE /tweet 엔드포인트 추가
# 요청 body: {"id": 유저ID, "tweet": "삭제할 트윗 내용"}
# 해당 유저의 해당 트윗을 app.tweets에서 제거
# 자기 트윗만 삭제 가능하도록 검증
# 앞에 POST가 DELETE로 달라지니 별 상관 없을거 같다

@app.route('/tweet', methods=['DELETE'])
def deltweet():
    payload = request.json
    user_id = int(payload['id'])
    tweet = payload['tweet']

    if user_id not in app.users:
        return '사용자가 존재하지 않습니다.', 400

    for tweets in app.tweets:
        if tweets['user_id'] == user_id and tweets['tweet'] == tweet:
            app.tweets.remove(tweets)
            return '삭제 완료', 200

    return '트윗 내용이 다르거나 아이디가 다릅니다.', 400

# 프로필 수정 API
# PUT /user/<int:user_id> 엔드포인트 추가
# name, email 변경 가능 (부분 수정 지원)
# password는 이 API로 변경 불가
# 변경된 유저 정보를 JSON으로 반환

@app.route('/user/<int:user_id>', methods=['PUT'])
def editprofile(user_id):
    if user_id not in app.users:
        return '사용자가 존재하지 않습니다.', 400

    editinfo = request.json

    if 'password' in editinfo:
        return '비밀번호는 변경할 수 없습니다.', 400

    if 'name' in editinfo:
        app.users[user_id]['name'] = editinfo['name']

    if 'email' in editinfo:
        app.users[user_id]['email'] = editinfo['email']

    return jsonify(app.users[user_id])

# 좋아요(Like) 시스템
# 트윗에 고유 ID를 부여하도록 구조 변경 (app.tweet_id_count 추가)
# POST /like - 특정 트윗에 좋아요
# POST /unlike - 좋아요 취소
# GET /tweet/<int:tweet_id> - 트윗 상세 조회 (좋아요 수 포함)

@app.route('/like', methods=['POST'])
def like():
    return 200

@app.route('/unlike', methods=['POST'])
def unlike():
    return 200

@app.route('/tweet/tweet_id', methods=['GET'])
def tweetinfo():
    return 200
