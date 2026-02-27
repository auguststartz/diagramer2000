AWS_REGIONS = [
    ("us-east-1", "US East (N. Virginia)"),
    ("us-east-2", "US East (Ohio)"),
    ("us-west-1", "US West (N. California)"),
    ("us-west-2", "US West (Oregon)"),
    ("af-south-1", "Africa (Cape Town)"),
    ("ca-central-1", "Canada (Central)"),
]

VALID_REGION_CODES = {code for code, _ in AWS_REGIONS}
