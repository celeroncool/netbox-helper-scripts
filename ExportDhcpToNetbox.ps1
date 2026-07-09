#Requires -Module DhcpServer

<#
.SYNOPSIS
    Exports all DHCP v4 scopes from a Windows DHCP server and writes a
    NetBox-compatible IP Range CSV for bulk import.

.PARAMETER DhcpServer
    FQDN or IP of the DHCP server. Defaults to localhost.

.PARAMETER OutputPath
    Destination CSV file. Defaults to .\netbox_ip_ranges.csv

.EXAMPLE
    .\Export-DhcpToNetBox.ps1 -DhcpServer dhcp01.corp.local -OutputPath C:\Temp\ranges.csv
#>

[CmdletBinding()]
param(
    [string]$DhcpServer  = $env:COMPUTERNAME,
    [string]$OutputPath  = '.\netbox_ip_ranges.csv'
)

# Convert dotted-decimal subnet mask to CIDR prefix length
function ConvertTo-PrefixLength {
    param([string]$SubnetMask)
    $octets = $SubnetMask -split '\.'
    $binary = ($octets | ForEach-Object { [Convert]::ToString([int]$_, 2).PadLeft(8,'0') }) -join ''
    return ($binary.ToCharArray() | Where-Object { $_ -eq '1' }).Count
}

# Map DHCP scope state to NetBox status token
function ConvertTo-NetBoxStatus {
    param([string]$State)
    switch ($State) {
        'Active'   { return 'active'   }
        default    { return 'reserved' }
    }
}

Write-Verbose "Querying DHCP server: $DhcpServer"
$scopes = Get-DhcpServerv4Scope -ComputerName $DhcpServer -ErrorAction Stop

if (-not $scopes) {
    Write-Warning "No scopes returned from $DhcpServer. Exiting."
    return
}

Write-Verbose "Found $($scopes.Count) scope(s). Building CSV rows..."

$rows = foreach ($scope in $scopes) {
    $prefix = ConvertTo-PrefixLength -SubnetMask $scope.SubnetMask.ToString()
    $status = ConvertTo-NetBoxStatus -State $scope.State.ToString()

    [PSCustomObject]@{
        start_address    = "$($scope.StartRange)/$prefix"
        end_address      = "$($scope.EndRange)/$prefix"
        status           = $status
        mark_populated   = 'true'
        mark_utilized    = 'true'
        description      = $scope.Name
        comments         = $scope.Description
    }
}

$rows | Export-Csv -Path $OutputPath -NoTypeInformation -Encoding UTF8
Write-Host "Exported $($rows.Count) IP range(s) to: $OutputPath"
