from configset import ConfigSet

# config = ConfigSet(config_file=r"traceback.json")
config = ConfigSet(config_file=r"docker-compose.yml")

config.show()
d = config.find("networks:cloud")
# d = config.find("DATA1:DATA2")
print(f"FOUND: {d}")

