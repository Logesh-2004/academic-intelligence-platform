def student_summary(df, reg_no):

    df.columns = df.columns.str.strip()

    stu = df[df["Register Number"].astype(str) == str(reg_no)]

    if stu.empty:
        return None

    # Safe fetch
    student_name = stu.iloc[0].get("Student Name", "Unknown")
    department = stu.iloc[0].get("Department", "Unknown")

    avg_internal = stu["Internal Mark"].mean()
    avg_external = stu["External Mark"].mean()
    avg_gp = stu["gp"].mean()

    weak_internal = stu[stu["Internal Mark"] < 35]
    high_gap = stu[stu["Internal-External Gap"] > 20]

    return {
        "student_name": student_name,
        "department": department,
        "avg_internal": round(avg_internal,2),
        "avg_external": round(avg_external,2),
        "avg_gp": round(avg_gp,2),
        "weak_subjects": weak_internal[["Course Code","Course Name","Internal Mark"]],
        "gap_subjects": high_gap[["Course Code","Course Name","Internal-External Gap"]],
        "raw": stu
    }
