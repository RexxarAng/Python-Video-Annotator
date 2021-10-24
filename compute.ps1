$dir1 = "./person1/"
$dir2 = "./person2/"
$script_path = "./interannotator.py"
$count = 0
$total_score = 0
$output_table = @()

Get-ChildItem ./person1/ -Filter "*.xml" | ForEach-Object {
    # Check if file exists
    If (Test-Path "$dir2/$($_.Name)") {
        #$(Write-Output "$dir1$($.Name) $dir2$($.Name)") # replace Write-Output to python script
        $current_score = $(python $script_path "$dir1$($_.Name)" "$dir2$($_.Name)")
#         Write-Output "$($_.Name) : $current_score"

        $properties = @{
            Filename = $($_.Name)
            Score = $current_score
        }
        $output_table += New-Object psobject -Property $properties
        $total_score += $current_score
        $count += 1
    }
}
$output_table
Write-Output ""
Write-Output "Total Average Score = $($total_score/$count)"
