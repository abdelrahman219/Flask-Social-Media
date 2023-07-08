import sys
from models import *

def update_null_privacy_posts():
    query = Post.update(privacy='public').where(Post.privacy >> None)
    query.execute()

def delete_all_posts():
    query = Post.delete()
    query.execute()

def delete_all_relationships():
    query = Relationship.delete()
    query.execute()

def delete_all_friendships():
    query = Friendship.delete()
    query.execute()

def delete_all_friends_lists():
    query = Friends_list.delete()
    query.execute()

# Additional functions...

# Run the specified function
if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Please provide a function name to execute.")
    else:
        function_name = sys.argv[1]
        if function_name == 'update_null_privacy_posts':
            update_null_privacy_posts()
        elif function_name == 'delete_all_posts':
            delete_all_posts()
        elif function_name == 'delete_all_relationships':
            delete_all_relationships()
        elif function_name == 'delete_all_friendships':
            delete_all_friendships()
        elif function_name == 'delete_all_friends_lists':
            delete_all_friends_lists()
        else:
            print("Invalid function name.")
# python db_test.py delete_all_friends_lists
