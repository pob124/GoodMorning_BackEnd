# 마이그레이션 통합 안내

## 통합 마이그레이션 파일

`unified_migration.py` 파일은 프로젝트의 모든 마이그레이션을 하나로 통합한 파일입니다. 이 파일은 다음 테이블을 생성합니다:

1. `users` - 사용자 정보를 저장하는 테이블
2. `chatrooms` - 채팅방 정보를 저장하는 테이블
3. `messages` - 채팅 메시지를 저장하는 테이블

## 사용 방법

새로운 데이터베이스 환경에서 애플리케이션을 실행하려면:

```bash
# alembic 명령 실행
alembic upgrade head
```

이 명령은 통합된 마이그레이션을 적용하여 모든 필요한 테이블을 한 번에 생성합니다.

## 기존 마이그레이션 파일

다음 마이그레이션 파일들이 하나로 통합되었습니다:

- `adc432ce2bca_create_user_table.py` - 사용자 테이블 생성
- `f27b67c54611_add_profile_fields_to_user_model.py` - 사용자 프로필 필드 추가
- `add_likes_column.py` - 좋아요 필드 추가
- `0632837ceea5_create_chatrooms_and_messages_tables.py` - 채팅방 관련 필드 수정
- `4abbcba98b66_create_chatrooms_and_messages_tables_.py` - 채팅방 및 메시지 테이블 생성
- `d76055d26879_create_messages_table.py` - 메시지 테이블 수정

이 파일들은 참고용으로 보관되며, 실제 마이그레이션에는 `unified_migration.py`만 사용됩니다. 