#!/usr/bin/env python3

import click
import unifi_switch_client

@click.group()
def cli():
    click.echo("ha")

@click.command()
def device_info():
    click.echo("device info")

cli.add_command(device_info)
