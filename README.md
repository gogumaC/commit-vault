# commit-vault

Sometimes we are so busy to commit.

But in same time we don't want to lose our strike or grass in the github.

This tool is saving your commit and automatically merge it in the main branch to protect your github strike.


## How does it work?

commit-vault will cherry pick your draft commint in draft bracnh

## How to start?

### 1. Folk this branch
### 2. Add secrets

It needs to add two secrete value.

1. GH_TOEKN

   You can get this token in
   Profile > settings > Developer Settings > Create classic token 

    You need to check 'repo' and 'user' scopre in Select Scopes section.
    Once you get the token, you need to copy it and paste it.

2. SSH_PRIVATE_KEY

    You need to authorize the github action cloud enviromnet.

    You have to create your own ssh-key

    ```
    ssh-keygen -t ed25519 -C "your_email@example.com"

    ```

    Then you can get two key file.

    - Private key: `~/.ssh/id_ed25519` (DO NOT UPLOAD THIS KEY)
    - Public key: `~/.ssh/id_ed25519.pub`

    What you need to do is just copy and paste Public key in your github  SSH and GPG keys pages.

    Then you need to paste your private key in the github secrete in your repository.


### 3. Set variables

You need to set two variables

- USER_EMAIL
- USER_NAME

commit-vault will commit the draft commit with these information.

This variables will be used in git configure command.

This will decide wich user are created the commit.


## How to use?

1. Create 'draft' branch in any your repository.
2. Add your new commit which you want to save in draft branch
3. The commit-vault will be triggered once a day (default : KST 23:30)
4. It will find a branch which has draft branch.
5. Once it find a branch with draft, I will check if there is new commit comparing with main.
6. If it has new commit, It will cherry-pick the updates to the main branch.
7. Then draft barnch will be rebased to the main.
8. Push main and draft
